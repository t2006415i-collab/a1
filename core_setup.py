import io
import json
import base64
import logging
import copy
import os
import time
import threading
from datetime import datetime
from urllib.parse import quote

from flask import Flask, request, jsonify, make_response, send_from_directory
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader, PdfWriter

import arabic_reshaper
from bidi.algorithm import get_display
from ftplib import FTP, all_errors as FTP_ALL_ERRORS

# --- Configuration Constants ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(threadName)s | %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

FONT_REGISTERED = False
REGISTERED_FONT_NAME = "CustomArabic"

OUTPUT_FOLDER = "output_jobs"
PAGES_PER_PART = 4 # Default value, now configurable
JOBS_DATA_FILE = "jobs_data.json"

MAX_RETRY = 3 # New: Maximum number of print retries

# --- Global Data Structures and Locks ---
PRINT_JOBS = [] # Master list of all jobs
CONTINUOUS_QUEUE = [] # Queue of job IDs for continuous printing (Producer-Consumer Queue)
QUEUE_LOCK = threading.Lock()
WORKER_THREAD = None # Reference to the persistent worker thread
WORKER_STOP_EVENT = threading.Event() # Event to signal the worker to stop

# --- Persistence Functions ---

def save_jobs_to_file():
    """Saves the PRINT_JOBS list to a JSON file in a thread-safe manner."""
    # NOTE: This function is expected to be called *while* holding the QUEUE_LOCK.
    try:
        # Use a temporary file for atomic write
        temp_path = JOBS_DATA_FILE + ".tmp"
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(PRINT_JOBS, f, ensure_ascii=False, indent=4)
        os.replace(temp_path, JOBS_DATA_FILE)
        logging.info(f"✅ تم حفظ {len(PRINT_JOBS)} وظيفة طباعة إلى {JOBS_DATA_FILE}.")
    except Exception as e:
        logging.error(f"❌ فشل حفظ وظائف الطباعة إلى {JOBS_DATA_FILE}: {e}", exc_info=True)

def load_jobs_from_file():
    """Loads the PRINT_JOBS list from a JSON file in a thread-safe manner."""
    global PRINT_JOBS
    if not os.path.exists(JOBS_DATA_FILE):
        logging.info(f"ℹ️ ملف {JOBS_DATA_FILE} غير موجود. بدء بقائمة وظائف فارغة.")
        return

    with QUEUE_LOCK:
        try:
            with open(JOBS_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    # Ensure new fields exist for compatibility/robustness
                    for job in data:
                        job.setdefault('retry_count', 0)
                        # Revert 'Printing' status to 'Ready' on startup crash recovery
                        if job['status'] == 'Printing':
                            job['status'] = 'Ready'
                            logging.warning(f"⚠️ تم إعادة تعيين حالة الوظيفة {job['id']} من 'Printing' إلى 'Ready' بعد تعطل الخادم.")

                    PRINT_JOBS = data
                    logging.info(f"✅ تم تحميل {len(PRINT_JOBS)} وظيفة طباعة من {JOBS_DATA_FILE}.")
                else:
                    logging.error(f"❌ محتوى {JOBS_DATA_FILE} غير صالح (ليس قائمة). بدء بقائمة فارغة.")
                    PRINT_JOBS = []
        except json.JSONDecodeError as e:
            logging.error(f"❌ فشل تحليل JSON في {JOBS_DATA_FILE}: {e}. بدء بقائمة فارغة.", exc_info=True)
            PRINT_JOBS = []
        except Exception as e:
            logging.error(f"❌ خطأ غير متوقع أثناء تحميل {JOBS_DATA_FILE}: {e}. بدء بقائمة فارغة.", exc_info=True)
            PRINT_JOBS = []

# --- Persistent Worker Thread Implementation (New Architecture) ---

def print_queue_worker():
    """
    Dedicated persistent worker thread for continuous printing (Consumer).
    It ensures continuous operation and manages job retries and flow control.
    """
    global CONTINUOUS_QUEUE
    while not WORKER_STOP_EVENT.is_set():
        job_id = None
        
        with QUEUE_LOCK:
            if CONTINUOUS_QUEUE:
                # Pop the next job ID from the front of the queue
                job_id = CONTINUOUS_QUEUE.pop(0)
            
        if job_id:
            logging.info(f"🔄 العامل المستمر: سحب مهمة الطباعة ID: {job_id} من قائمة الانتظار.")
            
            # Retrieve the full job data
            job_found = next((job for job in PRINT_JOBS if job['id'] == job_id), None)
            
            if not job_found:
                logging.error(f"❌ العامل المستمر: لم يتم العثور على بيانات الوظيفة ID: {job_id} في القائمة الرئيسية. تخطي.")
                continue

            # Check if the job is already being printed (Concurrency Guard)
            if job_found['status'] == 'Printing':
                logging.warning(f"⚠️ العامل المستمر: الوظيفة ID: {job_id} تم وضع علامة عليها بالفعل 'Printing'. تخطي (قد تكون قيد التشغيل بالفعل في موضوع آخر).")
                continue

            # Start the print job in a new non-recursive thread
            thread_name = f"FTP_Continuous_Print_{job_id}"
            ftp_thread = threading.Thread(
                target=print_job_ftp,
                args=(job_id, 
                      job_found.get('printer_ip'),
                      job_found.get('ftp_user'),
                      job_found.get('ftp_pwd', ''),
                      job_found.get('ring_number'),
                      True # is_continuous flag remains True for worker-initiated jobs
                      ),
                name=thread_name
            )
            ftp_thread.start()
        
        # Sleep for a few seconds to avoid tight loop CPU spin
        time.sleep(3)

def start_worker_thread():
    """Starts the persistent print queue worker thread."""
    global WORKER_THREAD
    if WORKER_THREAD is None or not WORKER_THREAD.is_alive():
        WORKER_THREAD = threading.Thread(target=print_queue_worker, name="PrintQueueWorker")
        WORKER_THREAD.daemon = True # Allow main thread to exit even if worker is running
        WORKER_THREAD.start()
        logging.info("🚀 بدأ تشغيل خيط العامل المستمر (PrintQueueWorker) بنجاح.")
    else:
        logging.info("ℹ️ خيط العامل المستمر قيد التشغيل بالفعل.")

# --- Utility Functions (Unchanged) ---

def register_custom_font(font_data: bytes) -> bool:
    global FONT_REGISTERED, REGISTERED_FONT_NAME
    if FONT_REGISTERED:
        return True
    try:
        font_stream = io.BytesIO(font_data)
        pdfmetrics.registerFont(TTFont(REGISTERED_FONT_NAME, font_stream))
        pdfmetrics.registerFontFamily(REGISTERED_FONT_NAME, normal=REGISTERED_FONT_NAME)
        FONT_REGISTERED = True
        logging.info("✅ تم تسجيل الخط العربي بنجاح.")
        return True
    except Exception as e:
        logging.error("❌ فشل تسجيل الخط: %s", e, exc_info=True)
        FONT_REGISTERED = False
        return False

def process_arabic_text(text: str) -> str:
    if not text or not text.strip():
        return ''
    try:
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        return bidi_text
    except Exception as e:
        logging.error("خطأ في معالجة النص العربي '%s': %s", text[:20], e)
        return text

def create_watermark(name: str, student_id: str, config: dict, font_data: bytes) -> io.BytesIO:
    font_available = register_custom_font(font_data)
    font_name = REGISTERED_FONT_NAME if font_available else 'Helvetica-Bold'
    font_size = 12
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    
    processed_name = process_arabic_text(name)
    processed_id = str(student_id)

    name_x = float(config.get('name_x', 375))
    name_y = float(config.get('name_y', 452.5))
    id_x = float(config.get('id_x', 400))
    id_y = float(config.get('id_y', 422.5))

    can.setFont(font_name, font_size)
    can.setFillColorRGB(0, 0, 0)
    can.drawRightString(name_x, name_y, processed_name)

    can.setFont(font_name, font_size)
    can.drawString(id_x, id_y, processed_id) 
    
    can.save()
    packet.seek(0)
    return packet

def split_pdf_ranges(job_id: str, pdf_data: io.BytesIO, pages_per_part: int) -> int:
    try:
        reader = PdfReader(pdf_data)
        total_pages = len(reader.pages)
        part_count = 0
        
        full_filename = f"{job_id}_FULL.pdf"
        # Ensure OUTPUT_FOLDER exists
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)
        
        with open(os.path.join(OUTPUT_FOLDER, full_filename), "wb") as f:
            pdf_data.seek(0)
            f.write(pdf_data.read())

        for i in range(0, total_pages, pages_per_part):
            writer = PdfWriter()
            end_page = min(i + pages_per_part, total_pages)
            for page_num in range(i, end_page):
                writer.add_page(reader.pages[page_num])
            
            part_count += 1
            part_filename = f"{job_id}_P{part_count:03}.pdf"
            with open(os.path.join(OUTPUT_FOLDER, part_filename), "wb") as f:
                writer.write(f)

        logging.info(f"✅ تم تقسيم المهمة {job_id} إلى {part_count} جزء.")
        return part_count

    except Exception as e:
        logging.error("❌ فشل تقسيم ملف PDF: %s", e, exc_info=True)
        return 0

# --- Core Printing Function (Modified) ---

def print_job_ftp(job_id: str, printer_ip: str, ftp_user: str, ftp_pwd: str, ring_number: str, is_continuous: bool = False):
    
    # 1. Retrieve and Validate Job State
    with QUEUE_LOCK:
        job_found = next((job for job in PRINT_JOBS if job['id'] == job_id), None)
        if not job_found:
            logging.error(f"❌ لم يتم العثور على الوظيفة ID: {job_id} للإرسال.")
            return

        # 2. Update Status to Printing
        job_found['status'] = 'Printing'
        job_found['start_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_jobs_to_file() # Persistence point B: Status change to Printing
        logging.info(f"🔄 بدأ إرسال مهمة الطباعة ID: {job_id} (محاولة: {job_found['retry_count'] + 1}) إلى الطابعة {printer_ip} برقم رينج: {ring_number}")
    
    ftp = None
    success_count = 0
    job_successful = False
    
    # FIX: Initialize error_detail here to avoid Pylint E0601 error 
    # when accessing it in the 'finally' block if job_successful is False.
    error_detail = "فشل غير محدد." 
    
    try:
        # 3. FTP Connection and File Transfer
        ftp = FTP(printer_ip, timeout=10)
        ftp.login(user=ftp_user, passwd=ftp_pwd)
        logging.info(f"✅ تم الاتصال بنجاح بالطابعة {printer_ip} عبر FTP.")

        all_files = os.listdir(OUTPUT_FOLDER)
        job_files = sorted([f for f in all_files if f.startswith(f"{job_id}_P")])
        
        if not job_files:
            raise FileNotFoundError(f"لم يتم العثور على ملفات جزئية للوظيفة {job_id}.")

        for filename in job_files:
            local_path = os.path.join(OUTPUT_FOLDER, filename)
            
            # Konica Minolta Bizhub 287 stapling command:
            staple_tag = "_STAPLE"
            ftp_filename = f"{filename[:-4]}{staple_tag}_R{ring_number}.pdf"
            
            logging.info(f"   ⬆️ جاري إرسال: {filename} باسم {ftp_filename}...")
            
            with open(local_path, 'rb') as f:
                ftp.storbinary(f'STOR {ftp_filename}', f)
            
            success_count += 1
            logging.info(f"   ✅ تم الإرسال بنجاح.")
        
        job_successful = True # Set flag for successful print
        
    except FTP_ALL_ERRORS as e:
        # Log FTP Error
        logging.error(f"❌ خطأ FTP أثناء إرسال مهمة الطباعة ID: {job_id}: %s", e, exc_info=True)
        error_detail = f"خطأ FTP: {e}"
    except FileNotFoundError as e:
        # Log File Error
        logging.error(f"❌ خطأ الملف أثناء إرسال مهمة الطباعة ID: {job_id}: %s", e, exc_info=True)
        error_detail = f"خطأ الملف: {e}"
    except Exception as e:
        # Log General Error
        logging.error(f"❌ خطأ غير متوقع أثناء إرسال مهمة الطباعة ID: {job_id}: %s", e, exc_info=True)
        error_detail = f"خطأ غير متوقع: {e}"
        
    finally:
        # 4. Final Job Status Update and Retry Logic
        if ftp:
            try:
                ftp.quit()
            except FTP_ALL_ERRORS:
                pass

        with QUEUE_LOCK:
            job_found = next((job for job in PRINT_JOBS if job['id'] == job_id), None)
            if not job_found: # Should not happen, but for safety
                return 

            if job_successful:
                # Success Logic
                job_found['status'] = 'Printed'
                job_found['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                job_found['print_details'] = f"تم الإرسال بنجاح ({success_count} ملف) إلى {printer_ip} بالرينج {ring_number}"
                logging.info(f"🎉 تم الانتهاء من إرسال مهمة الطباعة ID: {job_id}.")
            else:
                # Failure and Retry Logic
                job_found['end_time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                job_found['retry_count'] += 1
                job_found['print_details'] = error_detail # Usage is safe now
                
                if is_continuous and job_found['retry_count'] < MAX_RETRY:
                    # Reinsert at the start of the continuous queue for immediate retry
                    CONTINUOUS_QUEUE.insert(0, job_id)
                    job_found['status'] = 'Ready' # Set back to ready for the next attempt
                    logging.warning(f"🔄 فشل الطباعة ID: {job_id}. جاري إعادة إدراج الوظيفة في قائمة الانتظار للمحاولة {job_found['retry_count'] + 1}/{MAX_RETRY}.")
                else:
                    # Final failure or manual print failure
                    job_found['status'] = 'Error'
                    logging.error(f"❌ فشل الطباعة النهائي ID: {job_id} بعد {job_found['retry_count']} محاولات أو فشل الطباعة اليدوية.")
            
            # 5. Save State
            save_jobs_to_file() # Persistence point C: Final status/retry update