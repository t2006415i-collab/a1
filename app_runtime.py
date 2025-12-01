from core_setup import *

# Load jobs from file at startup
load_jobs_from_file()

# Start the dedicated worker thread immediately after loading jobs
start_worker_thread()

app = Flask(__name__)
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
    logging.info(f"📁 تم إنشاء مجلد المخرجات: {OUTPUT_FOLDER}")

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DocuMerge - منظومة</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {
            --shu-color: #dd2c53;
            --bg-color: #eef1f6;
            --card-color: #ffffff;
            --shadow-color: rgba(0, 0, 0, 0.15);
        }
        body {
            font-family: 'IBM Plex Sans Arabic', sans-serif;
            background-color: var(--bg-color);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 1rem;
        }
        .desktop-container {
            width: 100%;
            max-width: 1200px; /* Slightly wider for better layout */
            box-shadow: 0 10px 30px var(--shadow-color);
            border-radius: 1rem;
            overflow: hidden;
            background-color: var(--card-color);
            display: flex;
            min-height: 90vh;
        }
        .sidebar {
            background-color: var(--shu-color);
            color: white;
            width: 280px;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            padding: 2rem 1.5rem;
        }
        .sidebar-menu button {
            display: flex;
            align-items: center;
            width: 100%;
            padding: 0.75rem 1rem;
            margin-bottom: 0.5rem;
            border-radius: 0.5rem;
            text-align: right;
            transition: background-color 0.2s, opacity 0.2s;
            opacity: 0.7;
        }
        .sidebar-menu button:hover {
            opacity: 1;
            background-color: rgba(255, 255, 255, 0.1);
        }
        .sidebar-menu button.active {
            opacity: 1;
            background-color: rgba(255, 255, 255, 0.2);
            font-weight: 600;
        }
        .main-content {
            flex-grow: 1;
            padding: 2.5rem;
            overflow-y: auto;
        }
        .file-input-group {
            border: 2px dashed #ccc;
            border-radius: 0.5rem;
            padding: 1rem;
            cursor: pointer;
            transition: border-color 0.2s, background-color 0.2s;
            background-color: #fcfcfc;
        }
        .file-input-group:hover {
            border-color: var(--shu-color);
            background-color: #f0f8ff;
        }
        .file-input-group input[type="file"] {
            display: none;
        }
        .main-content::-webkit-scrollbar {
            width: 8px;
        }
        .main-content::-webkit-scrollbar-thumb {
            background: rgba(221, 44, 83, 0.5);
            border-radius: 10px;
        }
        .spinner {
            border: 4px solid rgba(255, 255, 255, 0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 1s linear infinite;
            margin-right: 0.5rem;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal-content {
            background: white;
            padding: 2rem;
            border-radius: 0.75rem;
            width: 90%;
            max-width: 500px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            transform: scale(0.95);
            transition: transform 0.3s ease-out;
        }
        .modal-overlay.open .modal-content {
            transform: scale(1);
        }
        @media (max-width: 1024px) {
            .desktop-container {
                max-height: none;
                min-height: 95vh;
                display: block;
            }
            .sidebar {
                width: 100%;
                padding: 1.5rem;
                height: auto;
                flex-direction: row;
                justify-content: space-around;
                align-items: center;
            }
            .sidebar-menu {
                display: flex;
                flex-direction: row;
                gap: 1rem;
            }
            .sidebar-menu button {
                width: auto;
                padding: 0.5rem 1rem;
                margin-bottom: 0;
            }
            .main-content {
                padding: 1.5rem;
            }
        }
    </style>
</head>
<body>
<div class="desktop-container">
    <div class="sidebar">
        <div>
            <div class="text-center">
                <div class="mb-4">
                    <img src="/static/shu_logo.jpg" width="100" height="100" class="mx-auto" style="color: white;" alt="Logo">
                </div>

                <h1 class="text-3xl font-bold mb-2">DocuMerge</h1>
                <p class="text-lg opacity-90 font-medium">منظومة إدارة المستندات</p>
                <div class="w-full h-px bg-white/40 my-6"></div>
            </div>
            <div class="sidebar-menu space-y-2">
                <button type="button" id="menu-merge" class="active" onclick="showSection('merge-section')">
                    <span data-lucide="zap" class="w-5 h-5 ml-3"></span>
                    عملية الدمج والمعالجة
                </button>
                <button type="button" id="menu-jobs" onclick="showSection('jobs-section'); loadPrintJobs();">
                    <span data-lucide="printer" class="w-5 h-5 ml-3"></span>
                    إدارة وظائف الطباعة
                </button>
            </div>
        </div>
        <p class="text-xs opacity-70 mt-8 text-center hidden lg:block">
            تم التطوير من قبل طه ادرا | <a href="mailto:2450041@shu.edu.ly">2450041@shu.edu.ly</a> | الإصدار 0.2 (تجريبي)
        </p>
    </div>

    <div class="main-content" id="merge-section">
        <h2 class="text-2xl font-bold text-gray-800 mb-8 border-b pb-2">تنفيذ عملية الدمج والتحضير للطباعة</h2>
        <form id="mergeForm" class="space-y-6">
            <div>
                <h3 class="text-xl font-semibold mb-3 text-gray-700 flex items-center">
                    <span data-lucide="folder-open" class="w-5 h-5 ml-2" style="color: var(--shu-color);"></span>
                    1. اختيار الملفات والخطوط
                </h3>
                <div class="grid md:grid-cols-2 gap-4">
                    <label class="file-input-group block" for="jsonFile">
                        <span class="flex items-center justify-between text-base font-medium text-gray-700">بيانات الطلاب (.json) <span data-lucide="file-json" class="w-5 h-5 text-gray-500"></span></span>
                        <input type="file" id="jsonFile" accept=".json" required>
                        <p class="text-xs text-gray-500 mt-1" id="jsonFileName">لم يتم اختيار ملف بعد</p>
                    </label>
                    <label class="file-input-group block" for="coverPdfFile">
                        <span class="flex items-center justify-between text-base font-medium text-gray-700">قالب الغلاف (.pdf) <span data-lucide="file-text" class="w-5 h-5 text-gray-500"></span></span>
                        <input type="file" id="coverPdfFile" accept=".pdf" required>
                        <p class="text-xs text-gray-500 mt-1" id="coverPdfFileName">لم يتم اختيار ملف بعد</p>
                    </label>
                    <label class="file-input-group block" for="examPdfFile">
                        <span class="flex items-center justify-between text-base font-medium text-gray-700">صفحات الامتحان الأساسية (.pdf) <span data-lucide="layers" class="w-5 h-5 text-gray-500"></span></span>
                        <input type="file" id="examPdfFile" accept=".pdf" required>
                        <p class="text-xs text-gray-500 mt-1" id="examPdfFileName">لم يتم اختيار ملف بعد</p>
                    </label>
                    <label class="file-input-group block" for="fontTtfFile">
                        <span class="flex items-center justify-between text-base font-medium text-gray-700">الخط العربي (.ttf) <span data-lucide="type" class="w-5 h-5 text-gray-500"></span></span>
                        <input type="file" id="fontTtfFile" accept=".ttf" required>
                        <p class="text-xs text-gray-500 mt-1" id="fontTtfFileName">يرجى اختيار خط TTF عربي</p>
                    </label>
                </div>
            </div>
            <div>
                <h3 class="text-xl font-semibold mb-3 text-gray-700 flex items-center">
                    <span data-lucide="settings" class="w-5 h-5 ml-2" style="color: var(--shu-color);"></span>
                    2. إعدادات الحقول والموقع (بالبكسل)
                </h3>
                <div class="grid md:grid-cols-2 gap-4 mb-4 p-4 rounded-lg border">
                    <h4 class="col-span-2 text-sm font-bold text-gray-700 mb-2">تحديد مفاتيح البيانات (من ملف JSON)</h4>
                    <div>
                        <label for="nameKey" class="block text-sm font-medium text-gray-600">مفتاح الاسم</label>
                        <input type="text" id="nameKey" value="name" class="mt-1 block w-full border border-gray-300 rounded-md p-2 text-center text-sm focus:ring-[var(--shu-color)] focus:border-[var(--shu-color)]">
                    </div>
                    <div>
                        <label for="idKey" class="block text-sm font-medium text-gray-600">مفتاح رقم القيد</label>
                        <input type="text" id="idKey" value="student_id" class="mt-1 block w-full border border-gray-300 rounded-md p-2 text-center text-sm focus:ring-[var(--shu-color)] focus:border-[var(--shu-color)]">
                    </div>
                    <h4 class="col-span-2 text-sm font-bold text-gray-700 mb-3 mt-4 border-t pt-3">مواقع الطباعة على الغلاف (نقطة الأصل: أسفل اليسار)</h4>
                    <p class="col-span-2 text-xs text-gray-500 mb-4">لصفحة A4: الإحداثي (X,Y) يمثل حافة الكتابة اليسرى لرقم القيد والحافة اليمنى للاسم.</p>
                    <div class="col-span-2 space-y-3">
                        <div class="grid grid-cols-3 gap-3 items-center">
                            <span class="col-span-1 text-sm font-semibold text-gray-600">الاسم (X/Y):</span>
                            <input type="number" id="nameX" value="375" placeholder="X" class="col-span-1 border border-gray-300 rounded-md p-2 text-center text-sm focus:ring-[var(--shu-color)] focus:border-[var(--shu-color)]">
                            <input type="number" id="nameY" value="452.5" placeholder="Y" class="col-span-1 border border-gray-300 rounded-md p-2 text-center text-sm focus:ring-[var(--shu-color)] focus:border-[var(--shu-color)]">
                        </div>
                        <div class="grid grid-cols-3 gap-3 items-center">
                            <span class="col-span-1 text-sm font-semibold text-gray-600">رقم القيد (X/Y):</span>
                            <input type="number" id="idX" value="400" placeholder="X" class="col-span-1 border border-gray-300 rounded-md p-2 text-center text-sm focus:ring-[var(--shu-color)] focus:border-[var(--shu-color)]">
                            <input type="number" id="idY" value="422.5" placeholder="Y" class="col-span-1 border border-gray-300 rounded-md p-2 text-center text-sm focus:ring-[var(--shu-color)] focus:border-[var(--shu-color)]">
                        </div>
                    </div>
                </div>
            </div>
            <div>
                <h3 class="text-xl font-semibold mb-3 text-gray-700 flex items-center">
                    <span data-lucide="scissors" class="w-5 h-5 ml-2" style="color: var(--shu-color);"></span>
                    3. إعدادات تقسيم الصفحات (جديد)
                </h3>
                <div class="p-4 rounded-lg border bg-gray-50">
                    <label for="pagesPerPart" class="block text-sm font-medium text-gray-700">عدد الصفحات لكل جزء طباعة (مثال: 4)</label>
                    <input type="number" id="pagesPerPart" value="4" min="1" required
                           class="mt-1 block w-full max-w-xs border border-gray-300 rounded-md p-2 text-center text-sm font-bold focus:ring-[var(--shu-color)] focus:border-[var(--shu-color)]">
                    <p class="text-xs text-gray-500 mt-1">سيتم تقسيم ملف PDF المدمج إلى أجزاء، كل جزء بحجم الصفحات المحدد. كل جزء يمثل مهمة طباعة مستقلة.</p>
                </div>
            </div>
            <div class="pt-6 border-t border-gray-200">
                <button type="submit" id="submitButton"
                        class="w-full flex items-center justify-center bg-[var(--shu-color)] text-white font-bold py-3 px-4 rounded-lg shadow-lg hover:bg-[#a92243] transition duration-300 disabled:opacity-50 disabled:cursor-not-allowed">
                    <span id="submitText">بدء عملية الدمج والتحضير للطباعة</span>
                    <div id="spinner" class="spinner hidden mr-3"></div>
                </button>
                <div id="statusMessage" role="alert" class="mt-4 p-3 rounded-lg text-sm text-center hidden font-medium"></div>
                <div id="connectionError" role="alert" class="mt-4 p-4 rounded-lg text-sm text-center bg-red-100 text-red-800 border-l-4 border-red-500 hidden font-medium">
                    <span data-lucide="alert-triangle" class="w-5 h-5 inline-block ml-2 align-middle"></span>
                    **خطأ في الاتصال:** يرجى التأكد من تشغيل الخادم والاتصال بالإنترنت
                </div>
            </div>
        </form>
    </div>
    
    <div class="main-content hidden" id="jobs-section">
        <h2 class="text-2xl font-bold text-gray-800 mb-8 border-b pb-2">إدارة ووظائف الطباعة الجاهزة</h2>
        
        <div class="p-4 rounded-lg border shadow-sm mb-6 bg-white">
            <h3 class="text-xl font-semibold mb-3 text-gray-700 flex items-center">
                <span data-lucide="fast-forward" class="w-5 h-5 ml-2 text-green-600"></span>
                تشغيل الطباعة المستمرة التلقائية (جديد)
            </h3>
            <p class="text-sm text-gray-600 mb-4">
                قم بتشغيل هذا الخيار لإرسال جميع المهام الجاهزة (Ready) في قائمة الانتظار إلى الطابعة تلقائيًا، واحدة تلو الأخرى، دون تدخل يدوي.
            </p>
            <form id="continuousPrintForm" class="space-y-4">
                <div class="grid md:grid-cols-2 gap-4">
                    <div>
                        <label for="contPrinterIp" class="block text-sm font-medium text-gray-700">عنوان IP الطابعة (FTP)</label>
                        <input type="text" id="contPrinterIp" value="192.168.1.50" required
                               class="mt-1 block w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-green-600 focus:border-green-600">
                    </div>
                    <div>
                        <label for="contRingNumber" class="block text-sm font-medium text-gray-700">رقم الرينج (Ring Number)</label>
                        <input type="number" id="contRingNumber" value="1" min="1" required
                               class="mt-1 block w-full border border-gray-300 rounded-md p-2 text-sm text-center font-bold focus:ring-green-600 focus:border-green-600">
                    </div>
                    <div class="md:col-span-2">
                        <label for="contFtpUser" class="block text-sm font-medium text-gray-700">اسم مستخدم FTP</label>
                        <input type="text" id="contFtpUser" value="anonymous" required
                               class="mt-1 block w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-green-600 focus:border-green-600">
                    </div>
                    <div class="md:col-span-2">
                        <label for="contFtpPwd" class="block text-sm font-medium text-gray-700">كلمة مرور FTP (اختياري)</label>
                        <input type="password" id="contFtpPwd" 
                               class="mt-1 block w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-green-600 focus:border-green-600">
                    </div>
                </div>
                <button type="submit" id="startContinuousButton"
                        class="w-full flex items-center justify-center bg-green-600 text-white font-bold py-3 px-4 rounded-lg shadow-lg hover:bg-green-700 transition duration-300 disabled:opacity-50 disabled:cursor-not-allowed">
                    <span data-lucide="play" class="w-5 h-5 ml-2"></span>
                    بدء الطباعة المستمرة لجميع المهام الجاهزة
                </button>
            </form>
        </div>

        <div id="jobsListContainer" class="space-y-4">
            <div class="bg-blue-50 border-l-4 border-blue-400 text-blue-800 p-4" role="alert">
                <p class="font-bold">جاري تحميل قائمة الوظائف...</p>
                <p class="text-sm">هذه القائمة تعرض جميع مهام الدمج التي تمت معالجتها وجاهزة للطباعة يدوياً أو تلقائياً عبر FTP.</p>
            </div>
        </div>
        <div id="jobsStatus" role="alert" class="mt-6 p-3 rounded-lg text-sm text-center hidden font-medium"></div>
    </div>
    <div id="printSettingsModal" class="modal-overlay hidden">
        <div class="modal-content">
            <h3 class="text-xl font-bold mb-4 flex items-center border-b pb-2">
                <span data-lucide="send" class="w-6 h-6 ml-2 text-[var(--shu-color)]"></span>
                إعدادات الطباعة اليدوية (FTP)
            </h3>
            <form id="ftpSettingsForm">
                <input type="hidden" id="modalJobId">
                <div class="space-y-4">
                    <div>
                        <label for="printerIp" class="block text-sm font-medium text-gray-700">عنوان IP الطابعة (FTP)</label>
                        <input type="text" id="printerIp" value="192.168.1.50" required
                               class="mt-1 block w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-[var(--shu-color)] focus:border-[var(--shu-color)]">
                    </div>
                    <div>
                        <label for="ftpUser" class="block text-sm font-medium text-gray-700">اسم مستخدم FTP</label>
                        <input type="text" id="ftpUser" value="anonymous" required
                               class="mt-1 block w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-[var(--shu-color)] focus:border-[var(--shu-color)]">
                    </div>
                    <div>
                        <label for="ftpPwd" class="block text-sm font-medium text-gray-700">كلمة مرور FTP (اختياري)</label>
                        <input type="password" id="ftpPwd" 
                               class="mt-1 block w-full border border-gray-300 rounded-md p-2 text-sm focus:ring-[var(--shu-color)] focus:border-[var(--shu-color)]">
                    </div>
                    <div>
                        <label for="ringNumber" class="block text-sm font-medium text-gray-700">رقم الرينج (Ring Number)</label>
                        <input type="number" id="ringNumber" value="1" min="1" required
                               class="mt-1 block w-full border border-gray-300 rounded-md p-2 text-sm text-center font-bold focus:ring-[var(--shu-color)] focus:border-[var(--shu-color)]">
                        <p class="text-xs text-gray-500 mt-1">يُستخدم لتمييز ملفات الطباعة باسم المستخدم/موقع الطباعة.</p>
                    </div>
                    <div id="modalStatus" role="alert" class="mt-4 p-3 rounded-lg text-sm text-center hidden font-medium"></div>
                </div>
                <div class="flex justify-end space-x-3 mt-6">
                    <button type="button" onclick="closeModal()"
                            class="px-4 py-2 text-sm font-medium rounded-md border border-gray-300 text-gray-700 hover:bg-gray-100 transition">
                        إلغاء
                    </button>
                    <button type="submit" id="modalSubmitButton"
                            class="px-4 py-2 text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 transition">
                        تأكيد الإرسال والبدء
                    </button>
                </div>
            </form>
        </div>
    </div>
    <script>
        lucide.createIcons();
        const API_URL_MERGE = '/api/merge';
        const API_URL_JOBS = '/api/jobs';
        const API_URL_DOWNLOAD = '/api/download/';
        const API_URL_CONTINUOUS = '/api/continuous_print';

        const localStorageKey = 'documerge_ftp_settings';
        const localStorageContKey = 'documerge_ftp_cont_settings';

        function loadFTPSettings() {
            const settings = localStorage.getItem(localStorageKey);
            if (settings) {
                return JSON.parse(settings);
            }
            return { printerIp: '192.168.1.50', ftpUser: 'anonymous', ringNumber: '1' };
        }

        function saveFTPSettings(ip, user, ring) {
            localStorage.setItem(localStorageKey, JSON.stringify({ printerIp: ip, ftpUser: user, ringNumber: ring }));
        }

        function loadContinuousSettings() {
            const settings = localStorage.getItem(localStorageContKey);
            if (settings) {
                return JSON.parse(settings);
            }
            return { contPrinterIp: '192.168.1.50', contFtpUser: 'anonymous', contRingNumber: '1' };
        }

        function saveContinuousSettings(ip, user, ring) {
            localStorage.setItem(localStorageContKey, JSON.stringify({ contPrinterIp: ip, contFtpUser: user, contRingNumber: ring }));
        }

        function fileToBase64(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(reader.result.split(',')[1]);
                reader.onerror = error => reject(error);
                reader.readAsDataURL(file);
            });
        }

        function updateStatus(message, type = 'info', targetId = 'statusMessage') {
            const statusDiv = document.getElementById(targetId);
            statusDiv.innerHTML = message;
            statusDiv.className = `mt-4 p-3 rounded-lg text-sm text-center font-medium`;
            statusDiv.classList.remove('hidden');
            if (type === 'success') {
                statusDiv.classList.add('bg-green-100', 'text-green-700');
            } else if (type === 'error') {
                statusDiv.classList.add('bg-red-100', 'text-red-700');
            } else if (type === 'warning') {
                statusDiv.classList.add('bg-yellow-100', 'text-yellow-700');
            } else {
                statusDiv.classList.add('bg-blue-100', 'text-blue-700');
            }
        }

        function setLoading(isLoading) {
            const button = document.getElementById('submitButton');
            const spinner = document.getElementById('spinner');
            const submitText = document.getElementById('submitText');
            button.disabled = isLoading;
            spinner.classList.toggle('hidden', !isLoading);
            submitText.textContent = isLoading ? 'جاري المعالجة... يرجى الانتظار' : 'بدء عملية الدمج والتحضير للطباعة';
        }

        function showSection(sectionId) {
            document.querySelectorAll('.main-content').forEach(section => {
                section.classList.add('hidden');
            });
            document.getElementById(sectionId).classList.remove('hidden');

            document.querySelectorAll('.sidebar-menu button').forEach(btn => {
                btn.classList.remove('active');
            });
            document.getElementById('menu-' + sectionId.replace('-section', '')).classList.add('active');
        }

        function openModal(jobId) {
            const settings = loadFTPSettings();
            document.getElementById('modalJobId').value = jobId;
            document.getElementById('printerIp').value = settings.printerIp;
            document.getElementById('ftpUser').value = settings.ftpUser;
            document.getElementById('ringNumber').value = settings.ringNumber;
            document.getElementById('ftpPwd').value = ''; 
            document.getElementById('modalStatus').classList.add('hidden');
            document.getElementById('printSettingsModal').classList.add('open');
            document.getElementById('printSettingsModal').classList.remove('hidden');
        }

        function closeModal() {
            document.getElementById('printSettingsModal').classList.remove('open');
            setTimeout(() => {
                document.getElementById('printSettingsModal').classList.add('hidden');
            }, 300);
        }

        async function loadPrintJobs() {
            const container = document.getElementById('jobsListContainer');
            updateStatus('جاري تحميل قائمة وظائف الطباعة...', 'info', 'jobsStatus');
            
            // Load continuous print settings into the form
            const contSettings = loadContinuousSettings();
            document.getElementById('contPrinterIp').value = contSettings.contPrinterIp;
            document.getElementById('contFtpUser').value = contSettings.contFtpUser;
            document.getElementById('contRingNumber').value = contSettings.contRingNumber;
            
            try {
                const response = await fetch(API_URL_JOBS);
                if (!response.ok) throw new Error('فشل في تحميل قائمة الوظائف');
                
                const jobs = await response.json();
                container.innerHTML = ''; 
                
                if (jobs.length === 0) {
                    container.innerHTML = '<div class="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-800 p-4" role="alert"><p class="font-bold">لا توجد مهام طباعة معالجة بعد.</p><p class="text-sm">ابدأ بـ "عملية الدمج والمعالجة" لإنشاء مهام جديدة.</p></div>';
                    updateStatus('لا توجد مهام طباعة حاليًا', 'warning', 'jobsStatus');
                    return;
                }
                
                jobs.forEach(job => {
                    const statusClass = job.status === 'Printed' ? 'bg-green-100 border-green-500 text-green-800' :
                                         job.status === 'Printing' ? 'bg-blue-100 border-blue-500 text-blue-800' :
                                         job.status === 'Error' ? 'bg-red-100 border-red-500 text-red-800' :
                                         'bg-gray-100 border-gray-500 text-gray-800';
                    
                    const statusIcon = job.status === 'Printed' ? 'check-circle' :
                                       job.status === 'Printing' ? 'loader-2' :
                                       job.status === 'Error' ? 'alert-triangle' :
                                       'alert-circle';
                    
                    const statusText = job.status === 'Printed' ? 'تمت الطباعة بنجاح' :
                                       job.status === 'Printing' ? 'جاري الإرسال للطابعة...' :
                                       job.status === 'Error' ? `❌ خطأ في الإرسال: ${job.print_details.split(':')[0]}` :
                                       'جاهز للطباعة';

                    const actionButton = job.status === 'Printing' ? `
                            <button disabled class="flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md text-white bg-gray-500 cursor-not-allowed">
                                <div class="spinner mr-2" style="width: 16px; height: 16px; border-top: 2px solid #fff;"></div>
                                جاري الإرسال
                            </button>
                        ` : `
                            <button onclick="handlePrintManualClick('${job.id}')"
                                    class="flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md text-white bg-[var(--shu-color)] hover:bg-[#a92243] transition">
                                <span data-lucide="send" class="w-4 h-4 ml-2"></span>
                                طباعة يدوية (FTP)
                            </button>
                        `;

                    const printTime = job.start_time && job.end_time ? 
                        `<p class="text-xs text-gray-500 mt-1">وقت الطباعة: ${new Date(job.start_time).toLocaleTimeString()} - ${new Date(job.end_time).toLocaleTimeString()}</p>` :
                        job.start_time ? `<p class="text-xs text-gray-500 mt-1">بدأ الإرسال: ${new Date(job.start_time).toLocaleTimeString()}</p>` : '';
                    
                    container.innerHTML += `
                        <div class="p-4 rounded-lg border-l-4 shadow-sm ${statusClass}">
                            <div class="flex justify-between items-start">
                                <div>
                                    <h4 class="font-bold text-lg">${job.filename}</h4>
                                    <p class="text-sm text-gray-600 mt-1">
                                        <span data-lucide="clock" class="w-4 h-4 inline-block ml-1"></span>
                                        تاريخ الإنشاء: ${job.timestamp}
                                    </p>
                                    <p class="text-sm text-gray-600 mt-1">
                                        <span data-lucide="file-text" class="w-4 h-4 inline-block ml-1"></span>
                                        عدد الأجزاء للطباعة: ${job.part_count}
                                    </p>
                                    ${printTime}
                                </div>
                                <div class="space-y-2 flex flex-col items-end">
                                    ${actionButton}
                                    <a href="${API_URL_DOWNLOAD}${job.id}" target="_blank"
                                        class="flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 transition">
                                        <span data-lucide="download" class="w-4 h-4 ml-2"></span>
                                        تحميل الملف الكامل
                                    </a>
                                </div>
                            </div>
                            <div class="mt-3 text-sm font-semibold flex items-center">
                                <span data-lucide="${statusIcon}" class="w-4 h-4 ml-2"></span>
                                ${statusText}
                                ${job.status === 'Error' ? `<span class="mr-2 text-xs text-red-600">(راجع السجلات)</span>` : ''}
                            </div>
                        </div>
                    `;
                    lucide.createIcons();
                });
                updateStatus(`تم تحميل ${jobs.length} وظيفة طباعة.`, 'success', 'jobsStatus');

            } catch (error) {
                console.error('Error loading jobs:', error);
                container.innerHTML = '<div class="bg-red-100 border-l-4 border-red-500 text-red-800 p-4" role="alert"><p class="font-bold">خطأ في تحميل الوظائف.</p><p class="text-sm">المرجع: ' + error.message + '</p></div>';
                updateStatus('فشل تحميل قائمة الوظائف', 'error', 'jobsStatus');
            }
        }

        function handlePrintManualClick(jobId) {
            openModal(jobId);
        }

        document.getElementById('ftpSettingsForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const jobId = document.getElementById('modalJobId').value;
            const printerIp = document.getElementById('printerIp').value.trim();
            const ftpUser = document.getElementById('ftpUser').value.trim();
            const ftpPwd = document.getElementById('ftpPwd').value;
            const ringNumber = document.getElementById('ringNumber').value.trim();

            if (!jobId || !printerIp || !ftpUser || !ringNumber) {
                updateStatus('يرجى ملء جميع الحقول المطلوبة (باستثناء كلمة المرور)', 'error', 'modalStatus');
                return;
            }
            
            saveFTPSettings(printerIp, ftpUser, ringNumber);

            closeModal();
            
            const payload = {
                job_id: jobId,
                printer_ip: printerIp,
                ftp_user: ftpUser,
                ftp_pwd: ftpPwd,
                ring_number: ringNumber,
                is_continuous: false // Manual print is not continuous
            };

            updateStatus(`جاري إرسال الوظيفة ID: ${jobId} إلى الطابعة ${printerIp} برقم رينج ${ringNumber}...`, 'info', 'jobsStatus');
            
            try {
                const response = await fetch(API_URL_JOBS, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    updateStatus(`تم بنجاح! بدأ إرسال مهمة الطباعة في الخلفية. (${result.message})`, 'success', 'jobsStatus');
                    loadPrintJobs(); 
                } else {
                    const errorJson = await response.json();
                    throw new Error(errorJson.error || 'فشل إرسال الطباعة');
                }
            } catch (error) {
                console.error('Manual Print Error:', error);
                updateStatus(`❌ فشل في الطباعة اليدوية: ${error.message}`, 'error', 'jobsStatus');
                loadPrintJobs(); 
            }
        });

        document.getElementById('continuousPrintForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const printerIp = document.getElementById('contPrinterIp').value.trim();
            const ftpUser = document.getElementById('contFtpUser').value.trim();
            const ftpPwd = document.getElementById('contFtpPwd').value;
            const ringNumber = document.getElementById('contRingNumber').value.trim();

            if (!printerIp || !ftpUser || !ringNumber) {
                updateStatus('يرجى ملء جميع حقول الطباعة المستمرة المطلوبة', 'error', 'jobsStatus');
                return;
            }
            
            saveContinuousSettings(printerIp, ftpUser, ringNumber);

            const payload = {
                printer_ip: printerIp,
                ftp_user: ftpUser,
                ftp_pwd: ftpPwd,
                ring_number: ringNumber
            };

            updateStatus(`جاري بدء الطباعة المستمرة لجميع المهام الجاهزة إلى الطابعة ${printerIp}...`, 'info', 'jobsStatus');
            
            try {
                const response = await fetch(API_URL_CONTINUOUS, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (response.ok) {
                    const result = await response.json();
                    updateStatus(`✅ تم بنجاح! بدأ خط الطباعة المستمر. (${result.message})`, 'success', 'jobsStatus');
                    loadPrintJobs(); 
                } else {
                    const errorJson = await response.json();
                    throw new Error(errorJson.error || 'فشل بدء الطباعة المستمرة');
                }
            } catch (error) {
                console.error('Continuous Print Error:', error);
                updateStatus(`❌ فشل في بدء الطباعة المستمرة: ${error.message}`, 'error', 'jobsStatus');
                loadPrintJobs(); 
            }
        });


        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', (e) => {
                const fileNameElement = document.getElementById(e.target.id + 'Name');
                if (e.target.files.length > 0) {
                    fileNameElement.textContent = e.target.files[0].name;
                    fileNameElement.classList.remove('text-gray-500');
                    fileNameElement.classList.add('text-[var(--shu-color)]', 'font-medium');
                } else {
                    const defaultText = e.target.id === 'fontTtfFile' ? 'يرجى اختيار خط TTF عربي' : 'لم يتم اختيار ملف بعد';
                    fileNameElement.textContent = defaultText;
                    fileNameElement.classList.remove('text-[var(--shu-color)]', 'font-medium');
                    fileNameElement.classList.add('text-gray-500');
                }
            });
        });

        document.getElementById('mergeForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            setLoading(true);
            document.getElementById('connectionError').classList.add('hidden');
            
            const jsonFile = document.getElementById('jsonFile').files[0];
            const coverPdfFile = document.getElementById('coverPdfFile').files[0];
            const examPdfFile = document.getElementById('examPdfFile').files[0];
            const fontTtfFile = document.getElementById('fontTtfFile').files[0];
            const pagesPerPart = document.getElementById('pagesPerPart').value.trim();

            if (!jsonFile || !coverPdfFile || !examPdfFile || !fontTtfFile || !pagesPerPart) {
                setLoading(false);
                updateStatus('يرجى اختيار جميع الملفات المطلوبة وإدخال عدد الصفحات لكل جزء', 'error');
                return;
            }

            try {
                updateStatus('جاري تحميل وقراءة الملفات...', 'info');

                const [json_data_b64, cover_pdf_b64, exam_pdf_b64, font_ttf_b64] = await Promise.all([
                    fileToBase64(jsonFile),
                    fileToBase64(coverPdfFile),
                    fileToBase64(examPdfFile),
                    fileToBase64(fontTtfFile)
                ]);

                const payload = {
                    json_data_b64,
                    cover_pdf_b64,
                    exam_pdf_b64,
                    font_ttf_b64,
                    pages_per_part: parseInt(pagesPerPart), // New field
                    config: {
                        name_key: document.getElementById('nameKey').value.trim(),
                        id_key: document.getElementById('idKey').value.trim(),
                        name_x: document.getElementById('nameX').value.trim(),
                        name_y: document.getElementById('nameY').value.trim(),
                        id_x: document.getElementById('idX').value.trim(),
                        id_y: document.getElementById('idY').value.trim(),
                    }
                };

                updateStatus('جاري إرسال البيانات إلى خادم المعالجة...', 'info');

                const response = await fetch(API_URL_MERGE, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (response.ok) {
                    const result = await response.json();
                    updateStatus('نجاح! تم الدمج. جاري تحضير ملف PDF للتحميل...', 'success');
                    
                    window.location.href = API_URL_DOWNLOAD + result.job_id;

                    document.getElementById('statusMessage').innerHTML = 
                        "<div class='p-4 bg-green-50 border border-green-300 rounded-lg text-green-800'>" +
                        "<h3 class='font-bold text-lg mb-1'>✔️ تمت عملية الدمج والتحميل بنجاح. الملف جاهز للطباعة.</h3>" +
                        "<p>تم تجهيز ملفات الطباعة في مجلد: <b>output_jobs</b></p>" +
                        "<p class='mt-2 text-sm text-gray-700'>✔ يمكنك الآن الذهاب إلى **إدارة وظائف الطباعة** لتحديد الإعدادات وبدء الطباعة يدوياً أو تلقائياً.</p>" +
                        "</div>";
                    
                    showSection('jobs-section');
                    loadPrintJobs();

                } else {
                    let errorMsg = 'فشل غير متوقع في المعالجة';
                    try {
                        const errorJson = await response.json();
                        errorMsg = errorJson.error || errorMsg;
                    } catch {
                        errorMsg = `خطأ في الخادم (الكود: ${response.status}).`;
                    }
                    updateStatus(`خطأ في الخادم: ${errorMsg}`, 'error');
                }
            } catch (error) {
                console.error('Network or General Error:', error);
                document.getElementById('connectionError').classList.remove('hidden');
                updateStatus('فشل في الاتصال، يرجى التحقق من تشغيل الخادم', 'error');
            } finally {
                setLoading(false);
            }
        });

        window.addEventListener('load', () => {
             fetch(API_URL_MERGE, { method: 'GET' })
                 .then(response => {
                     if (response.status === 200) {
                         updateStatus('تم الاتصال بنجاح مع الخادم. التطبيق جاهز', 'info');
                     } else {
                         updateStatus('تم الاتصال بنجاح مع الخادم. التطبيق جاهز', 'info');
                     }
                 })
                 .catch(error => {
                     console.error('Initial API check failed:', error);
                     document.getElementById('connectionError').classList.remove('hidden');
                     document.getElementById('submitButton').disabled = true;
                     updateStatus('فشل في الاتصال الأولي بخادم المعالجة. يرجى مراجعة إعدادات الخادم', 'error');
                 });
        });

    </script>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def index():
    return HTML_CONTENT

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

@app.route('/api/merge', methods=['GET', 'POST'])
def merge_documents():
    if request.method == 'GET':
        return jsonify({"status": "ready"}), 200
    
    try:
        data = request.json
        
        json_data_b64 = data['json_data_b64']
        cover_pdf_b64 = data['cover_pdf_b64']
        exam_pdf_b64 = data['exam_pdf_b64']
        font_ttf_b64 = data['font_ttf_b64']
        pages_per_part = data['pages_per_part']
        config = data['config']
        
        if not isinstance(pages_per_part, int) or pages_per_part < 1:
             return jsonify({"error": "عدد الصفحات لكل جزء يجب أن يكون رقمًا صحيحًا وموجبًا."}), 400

        json_data_bytes = base64.b64decode(json_data_b64)
        cover_pdf_bytes = base64.b64decode(cover_pdf_b64)
        exam_pdf_bytes = base64.b64decode(exam_pdf_b64)
        font_ttf_bytes = base64.b64decode(font_ttf_b64)

        students = json.loads(json_data_bytes)
        if not students:
            return jsonify({"error": "ملف بيانات الطلاب فارغ أو غير صالح."}), 400

        if not register_custom_font(font_ttf_bytes):
            return jsonify({"error": "فشل في تسجيل الخط العربي. يرجى التأكد من صلاحية ملف TTF."}), 400
        
        logging.info(f"بدء دمج {len(students)} طالب مع الغلاف وصفحات الامتحان...")
        
        exam_reader = PdfReader(io.BytesIO(exam_pdf_bytes))
        exam_pages = list(exam_reader.pages)
        
        final_pdf_writer = PdfWriter()
        
        for student in students:
            name = student.get(config['name_key'], 'غير متوفر')
            student_id = student.get(config['id_key'], 'غير متوفر')
            
            watermark_pdf = create_watermark(name, student_id, config, font_ttf_bytes)
            watermark_reader = PdfReader(watermark_pdf)
            watermark_page = watermark_reader.pages[0]
            
            cover_reader = PdfReader(io.BytesIO(cover_pdf_bytes))
            cover_page = copy.copy(cover_reader.pages[0])
            cover_page.merge_page(watermark_page)
            
            final_pdf_writer.add_page(cover_page)
            
            for page in exam_pages:
                final_pdf_writer.add_page(page)

        final_pdf_stream = io.BytesIO()
        final_pdf_writer.write(final_pdf_stream)
        final_pdf_stream.seek(0)

        job_id = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"Merged_Job_{job_id}.pdf"
        
        # Pass pages_per_part to the splitting function
        part_count = split_pdf_ranges(job_id, final_pdf_stream, pages_per_part)

        new_job = {
            "id": job_id,
            "filename": filename,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Ready",
            "part_count": part_count,
            "print_details": "لم يتم الإرسال بعد.",
            "full_path": os.path.join(OUTPUT_FOLDER, f"{job_id}_FULL.pdf"),
            "start_time": None, 
            "end_time": None,
            "retry_count": 0, # New field initialization
            # New fields for continuous print settings (must be initialized)
            "printer_ip": None,
            "ftp_user": None,
            "ftp_pwd": None,
            "ring_number": None
        }
        
        with QUEUE_LOCK:
            PRINT_JOBS.insert(0, new_job)
            save_jobs_to_file() # Persistence point A: New job insertion
        
        logging.info(f"✅ تم إنشاء وظيفة جديدة ID: {job_id} بـ {part_count} جزء. (تقسيم: {pages_per_part} صفحة/جزء)")

        return jsonify({"job_id": job_id, "message": "تم الدمج والتحضير بنجاح."}), 200

    except Exception as e:
        logging.error("❌ خطأ عام أثناء معالجة الدمج: %s", e, exc_info=True)
        return jsonify({"error": f"خطأ في معالجة الملفات: {e}"}), 500

@app.route('/api/jobs', methods=['GET', 'POST'])
def handle_jobs():
    if request.method == 'GET':
        with QUEUE_LOCK:
            return jsonify(PRINT_JOBS)
    
    elif request.method == 'POST':
        try:
            data = request.json
            job_id = data.get('job_id')
            printer_ip = data.get('printer_ip')
            ftp_user = data.get('ftp_user')
            ftp_pwd = data.get('ftp_pwd', '')
            ring_number = data.get('ring_number')
            is_continuous = data.get('is_continuous', False) 

            if not all([job_id, printer_ip, ftp_user, ring_number]):
                return jsonify({"error": "بيانات الطباعة ناقصة (Job ID، IP، المستخدم، أو رقم الرينج). يرجى التأكد من إدخالها."}), 400

            with QUEUE_LOCK:
                job_found = next((job for job in PRINT_JOBS if job['id'] == job_id), None)
            
            if not job_found:
                return jsonify({"error": "وظيفة الطباعة غير موجودة."}), 404
            
            if job_found['status'] == 'Printing':
                 return jsonify({"error": "هذه الوظيفة قيد الإرسال بالفعل."}), 409

            # Reset retry count for manual/explicit print
            with QUEUE_LOCK:
                job_found['retry_count'] = 0
                job_found['status'] = 'Ready'
                save_jobs_to_file()
            
            # Start the print job in a new thread
            thread_name = f"FTP_Print_{job_id}"
            ftp_thread = threading.Thread(
                target=print_job_ftp,
                args=(job_id, printer_ip, ftp_user, ftp_pwd, ring_number, is_continuous),
                name=thread_name
            )
            ftp_thread.start()
            
            return jsonify({
                "message": f"بدأ إرسال مهمة الطباعة ID: {job_id} إلى الطابعة ({printer_ip}) في الخلفية.",
                "thread_name": thread_name
            }), 200

        except Exception as e:
            logging.error("❌ خطأ في معالجة طلب الطباعة عبر FTP: %s", e, exc_info=True)
            return jsonify({"error": f"خطأ في بدء عملية الطباعة: {e}"}), 500

@app.route('/api/continuous_print', methods=['POST'])
def start_continuous_print():
    """
    Producer endpoint: Collects 'Ready' jobs, populates the queue,
    saves the printer configuration to the job entries, and relies on the 
    PrintQueueWorker to start consumption.
    """
    try:
        data = request.json
        printer_ip = data.get('printer_ip')
        ftp_user = data.get('ftp_user')
        ftp_pwd = data.get('ftp_pwd', '')
        ring_number = data.get('ring_number')

        if not all([printer_ip, ftp_user, ring_number]):
            return jsonify({"error": "بيانات الطباعة المستمرة ناقصة (IP، المستخدم، أو رقم الرينج). يرجى التأكد من إدخالها."}), 400

        job_ids_to_queue = []
        
        with QUEUE_LOCK:
            # 1. Identify and prepare 'Ready' jobs
            for job in PRINT_JOBS:
                if job['status'] == 'Ready' and job['id'] not in CONTINUOUS_QUEUE:
                    # Reset retry count and update print settings for the continuous run
                    job['retry_count'] = 0
                    job['printer_ip'] = printer_ip
                    job['ftp_user'] = ftp_user
                    job['ftp_pwd'] = ftp_pwd # Store credentials securely if needed, but here we store as-is
                    job['ring_number'] = ring_number
                    job_ids_to_queue.append(job['id'])
            
            if not job_ids_to_queue:
                return jsonify({"error": "لا توجد مهام طباعة جاهزة (Ready) في قائمة الانتظار لبدء الطباعة المستمرة."}), 404

            # 2. Add new ready jobs to the end of the continuous queue (FIFO)
            CONTINUOUS_QUEUE.extend(job_ids_to_queue)
            
            # 3. Save the updated job configurations
            save_jobs_to_file() 
            
            logging.info(f"تمت إضافة {len(job_ids_to_queue)} وظيفة إلى قائمة الانتظار المستمرة: {job_ids_to_queue}")

        # The worker thread will detect the non-empty queue and start processing immediately.
        return jsonify({
            "message": f"بدأ خط الطباعة المستمر. تمت إضافة {len(job_ids_to_queue)} مهمة إلى قائمة الانتظار للطباعة.",
        }), 200

    except Exception as e:
        logging.error("❌ خطأ في معالجة طلب الطباعة المستمرة: %s", e, exc_info=True)
        return jsonify({"error": f"خطأ في بدء عملية الطباعة المستمرة: {e}"}), 500


@app.route('/api/download/<job_id>', methods=['GET'])
def download_file(job_id):
    with QUEUE_LOCK:
        job_found = next((job for job in PRINT_JOBS if job['id'] == job_id), None)
    
    if not job_found:
        return jsonify({"error": "الملف غير موجود."}), 404
    
    full_filename = f"{job_id}_FULL.pdf"
    path = os.path.join(OUTPUT_FOLDER, full_filename)
    
    if not os.path.exists(path):
        return jsonify({"error": "ملف الـ PDF المدمج غير موجود على الخادم."}), 404

    response = make_response(send_from_directory(OUTPUT_FOLDER, full_filename, as_attachment=True))
    response.headers['Content-Disposition'] = f'attachment; filename="{quote(full_filename)}"'
    return response

if __name__ == '__main__':
    logging.info("🚀 تم بدء تشغيل خادم DocuMerge.")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)