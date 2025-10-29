// تهيئة Firebase
const firebaseConfig = {
    apiKey: "AIzaSyCIqGeesj-qUmbwxz0D0_Qj66NpRa-uUkI",
    authDomain: "gang-war-2.firebaseapp.com",
    databaseURL: "https://gang-war-2-default-rtdb.europe-west1.firebasedatabase.app",
    projectId: "gang-war-2",
    storageBucket: "gang-war-2.firebasestorage.app",
    messagingSenderId: "921173307781",
    appId: "1:921173307781:web:fd83197026a958275954ec",
    measurementId: "G-QY1T8DCBDS"
};

firebase.initializeApp(firebaseConfig);
const database = firebase.database();
const OWNER_CODE = "0643405204mm";

// البيانات الافتراضية المحسنة
const defaultData = {
    adminCodes: {
        "0643405204mm": {
            name: "مالك 👑 | 0643405204mm",
            used: false,
            isOwner: true
        },
        "EAGIES2025": {
            name: "مروان",
            used: false,
            isOwner: false
        }
    },
    gangs: {
        list: [
            {
                name: "البلود",
                points: 1,
                level: 0,
                pointsSources: [],
                logo: "https://via.placeholder.com/80x80/ff0000/ffffff?text=B"
            },
            {
                name: "المافيا",
                points: 0,
                level: 0,
                pointsSources: [],
                logo: "https://via.placeholder.com/80x80/000000/ffffff?text=M"
            },
            {
                name: "القروف ستريت",
                points: 0,
                level: 0,
                pointsSources: [],
                logo: "https://via.placeholder.com/80x80/800080/ffffff?text=G"
            },
            {
                name: "الكف الأسود",
                points: 0,
                level: 0,
                pointsSources: [],
                logo: "https://via.placeholder.com/80x80/333333/ffffff?text=K"
            },
            {
                name: "عائلة الرئيس",
                points: 0,
                level: 0,
                pointsSources: [],
                logo: "https://via.placeholder.com/80x80/ffd700/000000?text=R"
            }
        ]
    },
    rewards: {
        levels: [
            { level: 0, points: 0, maxMembers: 10, reward: "بداية العصابة" },
            { level: 1, points: 15, maxMembers: 13, reward: "تصريح استخدام جلوك للعصابة" },
            { level: 2, points: 35, maxMembers: 15, reward: "كاش 25 ألف للعصابة" },
            { level: 3, points: 60, maxMembers: 15, reward: "لا توجد جائزة" },
            { level: 4, points: 90, maxMembers: 17, reward: "لا توجد جائزة" },
            { level: 5, points: 125, maxMembers: 17, reward: "تصريح استخدام سلاح MP5 | كاش 30 ألف" },
            { level: 6, points: 165, maxMembers: 20, reward: "كاش 50 ألف للعصابة" },
            { level: 7, points: 210, maxMembers: 23, reward: "مقر للعصابة" },
            { level: 8, points: 260, maxMembers: 25, reward: "تصريح استخدام AK" },
            { level: 9, points: 315, maxMembers: 30, reward: "كاش 100 ألف للعصابة" },
            { level: 10, points: 375, maxMembers: 40, reward: "تصريح استخدام سلاح AS10 | +1 عدد في كل حالة سرقة" }
        ]
    },
    pointsMethods: [
        { name: "سرقة البقالة", points: 2, icon: "fas fa-store", description: "عملية سرقة بسيطة لكسب نقاط أساسية" },
        { name: "سطو البنك المركزي", points: 15, icon: "fas fa-university", description: "عملية عالية المخاطر والمكافآت" },
        { name: "مداهمة المحكمة", points: 12, icon: "fas fa-gavel", description: "تحدي قانوني خطير يتطلب تخطيط دقيق" },
        { name: "مداهمة مركز الشرطة", points: 18, icon: "fas fa-shield-alt", description: "مواجهة مباشرة مع السلطات" },
        { name: "مداهمة المراكز الحكومية", points: 10, icon: "fas fa-building", description: "عمليات استراتيجية ضد المؤسسات" },
        { name: "خطف القادة العليا", points: 25, icon: "fas fa-user-tie", description: "عمليات عالية الأهمية والخطورة" },
        { name: "مداهمة مقرات العصابات", points: 20, icon: "fas fa-crosshairs", description: "حروب مباشرة بين العصابات المتنافسة" },
        { name: "فوز في GANG WAR", points: 30, icon: "fas fa-trophy", description: "مكافأة الفوز في الحرب الأسبوعية" }
    ],
    appInfo: {
        content: `تطبيق GANG WAR هو نظام متقدم لإدارة العصابات يتيح لك مراقبة مستويات ونقاط كل عصابة، بالإضافة إلى الجوائز التي يمكن الحصول عليها. يتضمن التطبيق نظام GANG WAR أسبوعي بين العصابات يمنح نقاط للعصابات الفائزة.

الأنشطة المتاحة:
• سرقة البقالة: نشاط أساسي لكسب النقاط
• سطو البنك المركزي: عملية عالية المخاطر والمكافآت  
• مداهمة المحكمة: تحدي قانوني خطير
• مداهمة مركز الشرطة: مواجهة مباشرة مع السلطات
• مداهمة المراكز الحكومية: عمليات استراتيجية
• خطف القادة العليا: عمليات عالية الأهمية
• مداهمة مقرات العصابات: حروب مباشرة بين العصابات

جميع هذه الأنشطة تمنح نقاط متفاوتة حسب مستوى الصعوبة والمخاطرة.`
    },
    honors: {
        lastWinner: {
            gangName: "لم يتم تحديد فائز بعد",
            gangLogo: "https://via.placeholder.com/80x80/ff0000/ffffff?text=G",
            description: "في انتظار أول حرب"
        },
        topKiller: {
            playerName: "لم يتم تحديد بعد",
            playerAvatar: "https://via.placeholder.com/80x80/00ff00/ffffff?text=P",
            description: "في انتظار أول حرب"
        }
    },
    warTimer: {
        active: false,
        endTime: null,
        gang1: "",
        gang2: ""
    },
    notifications: {
        current: "مرحباً بكم في نظام إدارة العصابات المتقدم"
    }
};

// متغيرات عامة
let gangs = [];
let rewards = [];
let pointsMethods = [];
let infoLog = [];
let currentUser = null;
let isOwner = false;
let adminCodes = {};
let appInfo = {};
let honors = {};
let warTimer = {};
let notifications = {};
let codesVisible = true;
let warInterval = null;

// الأصوات
const sounds = {
    enter: () => playSound('https://www.soundjay.com/misc/sounds/bell-ringing-05.wav'),
    click: () => playSound('https://www.soundjay.com/misc/sounds/beep-07a.wav'),
    notification: () => playSound('https://www.soundjay.com/misc/sounds/bell-ringing-05.wav')
};

function playSound(url) {
    const audio = document.getElementById('audioPlayer');
    if (audio) {
        audio.src = url;
        audio.play().catch(e => console.log('تعذر تشغيل الصوت:', e));
    }
}

// تهيئة التطبيق
function initializeApp() {
    console.log('بدء تهيئة التطبيق...');
    
    // تحقق من وجود البيانات في Firebase
    database.ref().once('value').then((snapshot) => {
        if (!snapshot.exists() || !snapshot.val().gangs) {
            console.log('لا توجد بيانات، سيتم تحميل البيانات الافتراضية...');
            initializeDefaultData();
        }
        loadDataFromFirebase();
    });
}

// تحميل البيانات الافتراضية
function initializeDefaultData() {
    const updates = {};
    
    Object.keys(defaultData).forEach(key => {
        updates[key] = defaultData[key];
    });
    
    database.ref().update(updates).then(() => {
        console.log('تم تحميل البيانات الافتراضية بنجاح');
    }).catch((error) => {
        console.error('خطأ في تحميل البيانات:', error);
    });
}

// تحميل البيانات من Firebase
function loadDataFromFirebase() {
    // تحميل أكواد الأدمن
    database.ref('adminCodes').on('value', (snapshot) => {
        adminCodes = snapshot.val() || {};
        // تأكد من وجود كود المالك دائماً وأنه مالك
        if (!adminCodes[OWNER_CODE] || !adminCodes[OWNER_CODE].isOwner) {
            adminCodes[OWNER_CODE] = {
                name: "مالك 👑 | 0643405204mm",
                used: false,
                isOwner: true
            };
            database.ref('adminCodes').set(adminCodes);
        }
    });

    // تحميل العصابات
    database.ref('gangs').on('value', (snapshot) => {
        const data = snapshot.val();
        gangs = data?.list || defaultData.gangs.list;
        loadGangs();
        updateGangSelects();
    });

    // تحميل الجوائز
    database.ref('rewards').on('value', (snapshot) => {
        const data = snapshot.val();
        rewards = data?.levels || defaultData.rewards.levels;
        loadRewards();
        loadRewardsEditor();
    });

    // تحميل طرق النقاط
    database.ref('pointsMethods').on('value', (snapshot) => {
        pointsMethods = snapshot.val() || defaultData.pointsMethods;
        loadPointsMethods();
        loadPointsMethodsEditor();
    });

    // تحميل معلومات التطبيق
    database.ref('appInfo').on('value', (snapshot) => {
        appInfo = snapshot.val() || defaultData.appInfo;
        loadAppInfo();
    });

    // تحميل قسم التشريف
    database.ref('honors').on('value', (snapshot) => {
        honors = snapshot.val() || defaultData.honors;
        loadHonors();
    });

    // تحميل عداد الحرب
    database.ref('warTimer').on('value', (snapshot) => {
        warTimer = snapshot.val() || defaultData.warTimer;
        updateWarTimer();
    });

    // تحميل الإشعارات
    database.ref('notifications').on('value', (snapshot) => {
        notifications = snapshot.val() || defaultData.notifications;
        updateNotification();
    });

    // تحميل سجل المعلومات
    database.ref('infoLog').on('value', (snapshot) => {
        infoLog = snapshot.val() || [];
        updateInfoLogDisplay();
    });
}

// حفظ البيانات في Firebase
function saveDataToFirebase() {
    const updates = {
        'gangs/list': gangs,
        'adminCodes': adminCodes,
        'infoLog': infoLog
    };
    
    database.ref().update(updates).catch((error) => {
        console.error('خطأ في حفظ البيانات:', error);
        showNotification('حدث خطأ في حفظ البيانات', 'error');
    });
}

// دخول التطبيق
function enterApp() {
    sounds.enter();
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('mainApp').style.display = 'block';
    
    // تأثير دخول
    document.getElementById('mainApp').style.animation = 'fadeIn 0.8s ease-in';
    
    initializeApp();
}

// تبديل الشريط الجانبي
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// إخفاء القائمة الجانبية عند النقر خارجها
function hideSidebarOnClickOutside(event) {
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.querySelector('.sidebar-toggle');
    
    // التحقق من أن النقر ليس على القائمة الجانبية أو زر التبديل
    if (!sidebar.contains(event.target) && !sidebarToggle.contains(event.target)) {
        sidebar.classList.remove('open');
    }
}

// عرض الأقسام
function showSection(sectionName) {
    sounds.click();
    
    // إخفاء جميع الأقسام
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });

    // إزالة الفئة النشطة من جميع عناصر القائمة
    document.querySelectorAll('.menu-item').forEach(item => {
        item.classList.remove('active');
    });

    // عرض القسم المحدد
    document.getElementById(sectionName + 'Section').classList.add('active');

    // إضافة الفئة النشطة للعنصر المحدد
    event.target.classList.add('active');
    
    // إخفاء القائمة الجانبية على الهاتف بعد اختيار قسم
    const sidebar = document.getElementById('sidebar');
    if (window.innerWidth <= 1200) {
        sidebar.classList.remove('open');
    }
}

// حساب المستوى
function calculateLevel(points) {
    for (let i = rewards.length - 1; i >= 0; i--) {
        if (points >= rewards[i].points) {
            return i;
        }
    }
    return 0;
}

// تحميل العصابات
function loadGangs() {
    const gangsList = document.getElementById('gangsList');
    if (!gangsList) return;
    
    gangsList.innerHTML = '';

    // ترتيب العصابات حسب النقاط
    const sortedGangs = [...gangs].sort((a, b) => b.points - a.points);

    sortedGangs.forEach((gang, index) => {
        const gangElement = document.createElement('div');
        gangElement.className = 'gang-card';
        gangElement.onclick = () => showGangDetails(gang);

        const level = calculateLevel(gang.points);
        const currentLevelPoints = rewards[level]?.points || 0;
        const nextLevelPoints = rewards[level + 1]?.points || currentLevelPoints;
        const progress = nextLevelPoints > currentLevelPoints ? 
            ((gang.points - currentLevelPoints) / (nextLevelPoints - currentLevelPoints)) * 100 : 100;

        // تحديد نوع الترتيب
        let rankClass = '';
        let rankIcon = '';
        if (index === 0) {
            rankClass = 'first';
            rankIcon = '🥇';
        } else if (index === 1) {
            rankClass = 'second';
            rankIcon = '🥈';
        } else if (index === 2) {
            rankClass = 'third';
            rankIcon = '🥉';
        }

        gangElement.innerHTML = `
            <div class="gang-rank ${rankClass}">${rankIcon} #${index + 1}</div>
            <div class="gang-header">
                <div class="gang-logo">
                    <img src="${gang.logo || 'https://via.placeholder.com/60x60/ff0000/ffffff?text=G'}" alt="شعار ${gang.name}">
                </div>
                <div class="gang-info">
                    <h3>${gang.name}</h3>
                </div>
            </div>
            <div class="gang-stats">
                <div class="stat-item">
                    <span class="stat-label">النقاط:</span>
                    <span class="stat-value animate-count">${gang.points}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">المستوى:</span>
                    <span class="stat-value">${level}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">المكافأة:</span>
                    <span class="stat-value">${rewards[level]?.reward || 'غير محدد'}</span>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${Math.min(progress, 100)}%"></div>
            </div>
        `;

        gangsList.appendChild(gangElement);
        
        // تأثير ظهور متدرج
        setTimeout(() => {
            gangElement.style.animation = 'slideInUp 0.5s ease-out';
        }, index * 100);
    });
}

// البحث في العصابات
function searchGangs() {
    const searchTerm = document.getElementById('gangSearch').value.toLowerCase();
    const gangCards = document.querySelectorAll('.gang-card');
    
    gangCards.forEach(card => {
        const gangName = card.querySelector('.gang-info h3').textContent.toLowerCase();
        if (gangName.includes(searchTerm)) {
            card.style.display = 'block';
            card.classList.add('bounce');
            setTimeout(() => card.classList.remove('bounce'), 600);
        } else {
            card.style.display = 'none';
        }
    });
}

// عرض تفاصيل العصابة
function showGangDetails(gang) {
    document.getElementById('gangModalTitle').textContent = gang.name;
    
    const level = calculateLevel(gang.points);
    const nextLevel = level + 1;
    const currentLevelPoints = rewards[level]?.points || 0;
    const nextLevelPoints = rewards[nextLevel]?.points || null;

    let content = `
        <div class="gang-detail-item">
            <div class="gang-detail-label">النقاط الحالية</div>
            <div class="gang-detail-value">${gang.points}</div>
        </div>
        <div class="gang-detail-item">
            <div class="gang-detail-label">المستوى الحالي</div>
            <div class="gang-detail-value">${level} - ${rewards[level]?.reward || 'غير محدد'}</div>
        </div>
    `;

    if (nextLevelPoints) {
        const pointsNeeded = nextLevelPoints - gang.points;
        content += `
            <div class="gang-detail-item">
                <div class="gang-detail-label">النقاط المطلوبة للمستوى التالي</div>
                <div class="gang-detail-value">${pointsNeeded > 0 ? pointsNeeded : 0}</div>
            </div>
        `;
    }

    if (gang.pointsSources && gang.pointsSources.length > 0) {
        content += `
            <div class="gang-detail-item">
                <div class="gang-detail-label">مصادر النقاط الأخيرة</div>
                <div class="gang-detail-value">
        `;
        gang.pointsSources.slice(-5).forEach(source => {
            content += `
                <div class="points-source-item">
                    <strong>${source.points > 0 ? '+' : ''}${source.points}</strong> - ${source.reason}
                </div>
            `;
        });
        content += `</div></div>`;
    }

    document.getElementById('gangModalContent').innerHTML = content;
    document.getElementById('gangModal').classList.add('active');
}

// إغلاق النافذة المنبثقة
function closeGangModal() {
    document.getElementById('gangModal').classList.remove('active');
}

// تحميل الجوائز
function loadRewards() {
    const rewardsTableBody = document.getElementById('rewardsTableBody');
    if (!rewardsTableBody) return;
    
    rewardsTableBody.innerHTML = '';

    rewards.forEach((reward, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${index}</strong></td>
            <td><span class="stat-value">${reward.points}</span></td>
            <td><span class="stat-value">${reward.maxMembers}</span></td>
            <td>${reward.reward}</td>
        `;
        rewardsTableBody.appendChild(row);
    });
}

// تحميل طرق النقاط
function loadPointsMethods() {
    const pointsMethodsContainer = document.getElementById('pointsMethods');
    if (!pointsMethodsContainer) return;
    
    pointsMethodsContainer.innerHTML = '';

    pointsMethods.forEach(method => {
        const methodCard = document.createElement('div');
        methodCard.className = 'method-card';
        
        methodCard.innerHTML = `
            <div class="method-header">
                <div class="method-icon">
                    <i class="${method.icon}"></i>
                </div>
                <div class="method-title">${method.name}</div>
            </div>
            <div class="method-points">+${method.points} نقطة</div>
            <div class="method-description">${method.description}</div>
        `;
        
        pointsMethodsContainer.appendChild(methodCard);
    });
}

// تحميل معلومات التطبيق
function loadAppInfo() {
    const appInfoContainer = document.getElementById('appInfo');
    if (!appInfoContainer || !appInfo.content) return;
    
    appInfoContainer.innerHTML = `
        <div class="info-card">
            <h3>نبذة عن التطبيق</h3>
            <div style="white-space: pre-line;">${appInfo.content}</div>
        </div>
    `;
}

// تحميل قسم التشريف
function loadHonors() {
    const lastWinnerElement = document.getElementById('lastWinnerGang');
    const topKillerElement = document.getElementById('topKiller');
    
    if (lastWinnerElement && honors.lastWinner) {
        lastWinnerElement.innerHTML = `
            <div class="gang-logo">
                <img src="${honors.lastWinner.gangLogo}" alt="شعار العصابة">
            </div>
            <div class="gang-info">
                <h3>${honors.lastWinner.gangName}</h3>
                <p>${honors.lastWinner.description}</p>
            </div>
        `;
    }
    
    if (topKillerElement && honors.topKiller) {
        topKillerElement.innerHTML = `
            <div class="player-avatar">
                <img src="${honors.topKiller.playerAvatar}" alt="صورة اللاعب">
            </div>
            <div class="player-info">
                <h3>${honors.topKiller.playerName}</h3>
                <p>${honors.topKiller.description}</p>
            </div>
        `;
    }
}

// تحديث عداد الحرب
function updateWarTimer() {
    const timerDisplay = document.getElementById('timerDisplay');
    const warParticipants = document.getElementById('warParticipants');
    
    if (!timerDisplay || !warParticipants) return;
    
    if (warTimer.active && warTimer.endTime) {
        const endTime = new Date(warTimer.endTime).getTime();
        
        if (warInterval) clearInterval(warInterval);
        
        warInterval = setInterval(() => {
            const now = new Date().getTime();
            const distance = endTime - now;
            
            if (distance > 0) {
                const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                const seconds = Math.floor((distance % (1000 * 60)) / 1000);
                
                timerDisplay.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                warParticipants.textContent = `${warTimer.gang1} ضد ${warTimer.gang2}`;
                
                // إشعار قبل 5 دقائق
                if (distance <= 5 * 60 * 1000 && distance > 4 * 60 * 1000) {
                    showNotification('ستبدأ الحرب خلال 5 دقائق!', 'warning');
                    sounds.notification();
                }
            } else {
                timerDisplay.textContent = '00:00:00';
                warParticipants.textContent = 'بدأت الحرب!';
                showNotification('بدأت الحرب الآن!', 'success');
                sounds.notification();
                clearInterval(warInterval);
            }
        }, 1000);
    } else {
        timerDisplay.textContent = '00:00:00';
        warParticipants.textContent = 'لم يتم تحديد حرب بعد';
    }
}

// تحديث الإشعارات
function updateNotification() {
    const notificationText = document.getElementById('notificationText');
    if (notificationText && notifications.current) {
        notificationText.textContent = notifications.current;
    }
}

// إخفاء الإشعار
function hideNotification() {
    document.getElementById('notificationBar').style.display = 'none';
}

// عرض إشعار مؤقت
function showNotification(message, type = 'info') {
    const notificationBar = document.getElementById('notificationBar');
    const notificationText = document.getElementById('notificationText');
    
    if (notificationBar && notificationText) {
        notificationText.textContent = message;
        notificationBar.style.display = 'flex';
        notificationBar.className = `notification-bar ${type}`;
        
        // إخفاء تلقائي بعد 5 ثوان
        setTimeout(() => {
            notificationBar.style.display = 'none';
        }, 5000);
    }
}

// إضافة سجل معلومات
function addInfoLog(action, user) {
    const now = new Date();
    const logEntry = {
        time: now.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        }),
        user: user,
        action: action,
        timestamp: Date.now()
    };
    
    infoLog.unshift(logEntry);
    
    // الاحتفاظ بآخر 100 إدخال فقط
    if (infoLog.length > 100) {
        infoLog = infoLog.slice(0, 100);
    }
    
    updateInfoLogDisplay();
    saveDataToFirebase();
}

// تحديث عرض سجل المعلومات
function updateInfoLogDisplay() {
    const infoLogDisplay = document.getElementById('infoLogDisplay');
    if (!infoLogDisplay) return;
    
    infoLogDisplay.innerHTML = '';
    
    if (infoLog.length === 0) {
        infoLogDisplay.innerHTML = '<div class="log-item">لا توجد عمليات مسجلة</div>';
        return;
    }
    
    infoLog.slice(0, 20).forEach(log => {
        const logItem = document.createElement('div');
        logItem.className = 'log-item';
        logItem.innerHTML = `
            <div class="log-time">${log.time}</div>
            <div class="log-user">${log.user}</div>
            <div class="log-action">${log.action}</div>
        `;
        infoLogDisplay.appendChild(logItem);
    });
}

// تسجيل دخول الأدمن
function adminLogin() {
    const code = document.getElementById('adminCode').value.trim();
    
    if (adminCodes[code]) {
        const adminData = adminCodes[code];
        
        currentUser = adminData.name;
        isOwner = adminData.isOwner || (code === OWNER_CODE);
        
        document.getElementById('adminLogin').style.display = 'none';
        document.getElementById('adminActions').style.display = 'block';
        
        // عرض رسالة الترحيب
        const welcomeMsg = `مرحباً ${currentUser}`;
        const badge = isOwner ? '<span class="badge owner">👑 مالك</span>' : '<span class="badge admin">🛡️ أدمن</span>';
        document.getElementById('adminWelcome').innerHTML = welcomeMsg + badge;
        
        // عرض تبويب الأكواد للمالك فقط
        const codesTab = document.getElementById('codesTab');
        const codesManagement = document.getElementById('codes-management');
        if (isOwner) {
            codesTab.style.display = 'flex';
            codesManagement.classList.add('show');
            displayAdminCodes();
        } else {
            codesTab.style.display = 'none';
            codesManagement.classList.remove('show');
        }
        
        updateGangSelects();
        addInfoLog(`تسجيل دخول بنجاح`, currentUser);
        
        showNotification(`مرحباً ${currentUser}!`, 'success');
        sounds.click();
    } else {
        showNotification('كود خاطئ!', 'error');
        document.getElementById('adminCode').classList.add('shake');
        setTimeout(() => {
            document.getElementById('adminCode').classList.remove('shake');
        }, 500);
    }
}

// عرض تبويبات الإدارة
function showAdminTab(tabName) {
    sounds.click();
    
    // إخفاء جميع التبويبات
    document.querySelectorAll('.tab-panel').forEach(panel => {
        panel.classList.remove('active');
    });
    
    // إزالة الفئة النشطة من جميع الأزرار
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // عرض التبويب المحدد
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
}

// تحديث قوائم العصابات
function updateGangSelects() {
    const selects = ['gangSelect', 'warGang1', 'warGang2', 'winnerGang'];
    
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = '';
            gangs.forEach((gang, index) => {
                const option = document.createElement('option');
                option.value = index;
                option.textContent = gang.name;
                select.appendChild(option);
            });
        }
    });
}

// تحديث نقاط العصابة
function updateGangPoints() {
    const gangIndex = document.getElementById('gangSelect').value;
    const points = parseInt(document.getElementById('pointsInput').value);
    const reason = document.getElementById('reasonInput').value.trim();
    
    if (isNaN(points)) {
        showNotification('يرجى إدخال رقم صحيح!', 'error');
        return;
    }
    
    if (!reason) {
        showNotification('يرجى إدخال سبب التعديل!', 'error');
        return;
    }
    
    const gang = gangs[gangIndex];
    gang.points = Math.max(0, gang.points + points);
    gang.level = calculateLevel(gang.points);
    
    // إضافة مصدر النقاط
    if (!gang.pointsSources) {
        gang.pointsSources = [];
    }
    gang.pointsSources.push({
        points: points,
        reason: reason,
        timestamp: new Date().toISOString(),
        admin: currentUser
    });
    
    // إضافة سجل المعلومات
    const action = points > 0 ? 
        `أضاف ${points} نقطة لعصابة ${gang.name} - السبب: ${reason}` :
        `أزال ${Math.abs(points)} نقطة من عصابة ${gang.name} - السبب: ${reason}`;
    addInfoLog(action, currentUser);
    
    // حفظ البيانات
    saveDataToFirebase();
    
    document.getElementById('pointsInput').value = '';
    document.getElementById('reasonInput').value = '';
    
    showNotification('تم تحديث النقاط بنجاح!', 'success');
    sounds.click();
}

// تحديث اسم العصابة
function updateGangName() {
    const gangIndex = document.getElementById('gangSelect').value;
    const newName = document.getElementById('gangNameInput').value.trim();
    
    if (!newName) {
        showNotification('يرجى إدخال اسم صحيح!', 'error');
        return;
    }
    
    const oldName = gangs[gangIndex].name;
    gangs[gangIndex].name = newName;
    
    addInfoLog(`غير اسم العصابة من "${oldName}" إلى "${newName}"`, currentUser);
    saveDataToFirebase();
    
    document.getElementById('gangNameInput').value = '';
    updateGangSelects();
    
    showNotification('تم تحديث اسم العصابة بنجاح!', 'success');
    sounds.click();
}

// رفع شعار العصابة
function uploadGangLogo() {
    const gangIndex = document.getElementById('gangSelect').value;
    const file = document.getElementById('gangLogoInput').files[0];
    
    if (!file) return;
    
    // في التطبيق الحقيقي، ستحتاج لرفع الصورة إلى خدمة تخزين
    // هنا سنستخدم URL مؤقت للعرض
    const reader = new FileReader();
    reader.onload = function(e) {
        gangs[gangIndex].logo = e.target.result;
        saveDataToFirebase();
        showNotification('تم تحديث شعار العصابة بنجاح!', 'success');
    };
    reader.readAsDataURL(file);
}

// إضافة عصابة جديدة
function addNewGang() {
    const newName = document.getElementById('newGangInput').value.trim();
    
    if (!newName) {
        showNotification('يرجى إدخال اسم العصابة!', 'error');
        return;
    }
    
    gangs.push({ 
        name: newName, 
        points: 0, 
        level: 0, 
        pointsSources: [],
        logo: "https://via.placeholder.com/80x80/ff0000/ffffff?text=" + newName.charAt(0)
    });
    
    addInfoLog(`أضاف عصابة جديدة: "${newName}"`, currentUser);
    saveDataToFirebase();
    
    document.getElementById('newGangInput').value = '';
    updateGangSelects();
    
    showNotification('تم إضافة العصابة بنجاح!', 'success');
    sounds.click();
}

// حذف العصابة
function deleteGang() {
    const gangIndex = document.getElementById('gangSelect').value;
    const gangName = gangs[gangIndex].name;
    
    if (confirm(`هل أنت متأكد من حذف عصابة "${gangName}"؟`)) {
        gangs.splice(gangIndex, 1);
        
        addInfoLog(`حذف عصابة: "${gangName}"`, currentUser);
        saveDataToFirebase();
        
        updateGangSelects();
        showNotification('تم حذف العصابة بنجاح!', 'success');
        sounds.click();
    }
}

// تحميل محرر الجوائز
function loadRewardsEditor() {
    const rewardsEditor = document.getElementById('rewardsEditor');
    if (!rewardsEditor) return;
    
    rewardsEditor.innerHTML = '';
    
    rewards.forEach((reward, index) => {
        const rewardItem = document.createElement('div');
        rewardItem.className = 'form-group';
        rewardItem.innerHTML = `
            <label>المستوى ${index}:</label>
            <div class="form-row">
                <div class="form-group">
                    <input type="number" value="${reward.points}" onchange="updateReward(${index}, 'points', this.value)" placeholder="النقاط">
                </div>
                <div class="form-group">
                    <input type="number" value="${reward.maxMembers}" onchange="updateReward(${index}, 'maxMembers', this.value)" placeholder="الأعضاء">
                </div>
                <div class="form-group">
                    <input type="text" value="${reward.reward}" onchange="updateReward(${index}, 'reward', this.value)" placeholder="المكافأة">
                </div>
            </div>
        `;
        rewardsEditor.appendChild(rewardItem);
    });
}

// تحديث جائزة
function updateReward(index, field, value) {
    if (field === 'points' || field === 'maxMembers') {
        rewards[index][field] = parseInt(value) || 0;
    } else {
        rewards[index][field] = value;
    }
}

// حفظ الجوائز
function saveRewards() {
    database.ref('rewards/levels').set(rewards).then(() => {
        showNotification('تم حفظ الجوائز بنجاح!', 'success');
        addInfoLog('حدث الجوائز والمستويات', currentUser);
    }).catch((error) => {
        showNotification('خطأ في حفظ الجوائز', 'error');
    });
}

// تحميل محرر طرق النقاط
function loadPointsMethodsEditor() {
    const editor = document.getElementById('pointsMethodsEditor');
    if (!editor) return;
    
    editor.innerHTML = '';
    
    pointsMethods.forEach((method, index) => {
        const methodItem = document.createElement('div');
        methodItem.className = 'form-group';
        methodItem.innerHTML = `
            <label>${method.name}:</label>
            <div class="form-row">
                <div class="form-group">
                    <input type="text" value="${method.name}" onchange="updatePointsMethod(${index}, 'name', this.value)" placeholder="اسم الطريقة">
                </div>
                <div class="form-group">
                    <input type="number" value="${method.points}" onchange="updatePointsMethod(${index}, 'points', this.value)" placeholder="النقاط">
                </div>
                <div class="form-group">
                    <textarea onchange="updatePointsMethod(${index}, 'description', this.value)" placeholder="الوصف">${method.description}</textarea>
                </div>
            </div>
        `;
        editor.appendChild(methodItem);
    });
}

// تحديث طريقة النقاط
function updatePointsMethod(index, field, value) {
    if (field === 'points') {
        pointsMethods[index][field] = parseInt(value) || 0;
    } else {
        pointsMethods[index][field] = value;
    }
}

// حفظ طرق النقاط
function savePointsMethods() {
    database.ref('pointsMethods').set(pointsMethods).then(() => {
        showNotification('تم حفظ طرق النقاط بنجاح!', 'success');
        addInfoLog('حدث طرق الحصول على النقاط', currentUser);
    }).catch((error) => {
        showNotification('خطأ في حفظ طرق النقاط', 'error');
    });
}

// حفظ معلومات التطبيق
function saveAppInfo() {
    const content = document.getElementById('appInfoEditor').value;
    
    database.ref('appInfo/content').set(content).then(() => {
        showNotification('تم حفظ معلومات التطبيق بنجاح!', 'success');
        addInfoLog('حدث معلومات التطبيق', currentUser);
    }).catch((error) => {
        showNotification('خطأ في حفظ معلومات التطبيق', 'error');
    });
}

// إرسال إشعار
function sendNotification() {
    const message = document.getElementById('notificationInput').value.trim();
    
    if (!message) {
        showNotification('يرجى إدخال نص الإشعار!', 'error');
        return;
    }
    
    database.ref('notifications/current').set(message).then(() => {
        showNotification('تم إرسال الإشعار بنجاح!', 'success');
        addInfoLog(`أرسل إشعار عام: "${message}"`, currentUser);
        document.getElementById('notificationInput').value = '';
    }).catch((error) => {
        showNotification('خطأ في إرسال الإشعار', 'error');
    });
}

// جدولة حرب
function scheduleWar() {
    const gang1Index = document.getElementById('warGang1').value;
    const gang2Index = document.getElementById('warGang2').value;
    const warDate = document.getElementById('warDate').value;
    const warTime = document.getElementById('warTime').value;
    
    if (gang1Index === gang2Index) {
        showNotification('لا يمكن أن تحارب العصابة نفسها!', 'error');
        return;
    }
    
    if (!warDate || !warTime) {
        showNotification('يرجى تحديد تاريخ ووقت الحرب!', 'error');
        return;
    }
    
    const endTime = new Date(`${warDate}T${warTime}`).toISOString();
    const gang1Name = gangs[gang1Index].name;
    const gang2Name = gangs[gang2Index].name;
    
    const warData = {
        active: true,
        endTime: endTime,
        gang1: gang1Name,
        gang2: gang2Name
    };
    
    database.ref('warTimer').set(warData).then(() => {
        showNotification(`تم جدولة حرب بين ${gang1Name} و ${gang2Name}!`, 'success');
        addInfoLog(`جدول حرب بين ${gang1Name} و ${gang2Name} في ${warDate} ${warTime}`, currentUser);
    }).catch((error) => {
        showNotification('خطأ في جدولة الحرب', 'error');
    });
}

// بدء حرب فورية
function startWar() {
    const gang1Index = document.getElementById('warGang1').value;
    const gang2Index = document.getElementById('warGang2').value;
    
    if (gang1Index === gang2Index) {
        showNotification('لا يمكن أن تحارب العصابة نفسها!', 'error');
        return;
    }
    
    const gang1Name = gangs[gang1Index].name;
    const gang2Name = gangs[gang2Index].name;
    
    const warData = {
        active: true,
        endTime: new Date(Date.now() + 60 * 60 * 1000).toISOString(), // ساعة واحدة
        gang1: gang1Name,
        gang2: gang2Name
    };
    
    database.ref('warTimer').set(warData).then(() => {
        showNotification(`بدأت الحرب بين ${gang1Name} و ${gang2Name}!`, 'success');
        addInfoLog(`بدأ حرب فورية بين ${gang1Name} و ${gang2Name}`, currentUser);
        sounds.notification();
    }).catch((error) => {
        showNotification('خطأ في بدء الحرب', 'error');
    });
}

// إنهاء حرب
function endWar() {
    const warData = {
        active: false,
        endTime: null,
        gang1: "",
        gang2: ""
    };
    
    database.ref('warTimer').set(warData).then(() => {
        showNotification('تم إنهاء الحرب!', 'success');
        addInfoLog('أنهى الحرب الحالية', currentUser);
    }).catch((error) => {
        showNotification('خطأ في إنهاء الحرب', 'error');
    });
}

// حفظ نتائج الحرب
function saveWarResults() {
    const winnerIndex = document.getElementById('winnerGang').value;
    const topKillerName = document.getElementById('topKillerName').value.trim();
    const topKillerAvatar = document.getElementById('topKillerAvatar').value.trim();
    
    if (!topKillerName) {
        showNotification('يرجى إدخال اسم أعلى قاتل!', 'error');
        return;
    }
    
    const winnerGang = gangs[winnerIndex];
    
    // إضافة نقاط للعصابة الفائزة
    winnerGang.points += 30;
    winnerGang.level = calculateLevel(winnerGang.points);
    
    if (!winnerGang.pointsSources) {
        winnerGang.pointsSources = [];
    }
    winnerGang.pointsSources.push({
        points: 30,
        reason: 'فوز في GANG WAR',
        timestamp: new Date().toISOString(),
        admin: currentUser
    });
    
    // تحديث قسم التشريف
    const honorsData = {
        lastWinner: {
            gangName: winnerGang.name,
            gangLogo: winnerGang.logo || "https://via.placeholder.com/80x80/ff0000/ffffff?text=G",
            description: `فائز آخر حرب - ${new Date().toLocaleDateString('en-US')}`
        },
        topKiller: {
            playerName: topKillerName,
            playerAvatar: topKillerAvatar || "https://via.placeholder.com/80x80/00ff00/ffffff?text=P",
            description: `أعلى قاتل في آخر حرب - ${new Date().toLocaleDateString('en-US')}`
        }
    };
    
    // حفظ البيانات
    const updates = {
        'gangs/list': gangs,
        'honors': honorsData,
        'warTimer': {
            active: false,
            endTime: null,
            gang1: "",
            gang2: ""
        }
    };
    
    database.ref().update(updates).then(() => {
        showNotification(`تم حفظ نتائج الحرب! فازت عصابة ${winnerGang.name}`, 'success');
        addInfoLog(`حفظ نتائج الحرب - الفائز: ${winnerGang.name}, أعلى قاتل: ${topKillerName}`, currentUser);
        
        // مسح النموذج
        document.getElementById('topKillerName').value = '';
        document.getElementById('topKillerAvatar').value = '';
    }).catch((error) => {
        showNotification('خطأ في حفظ نتائج الحرب', 'error');
    });
}

// إضافة كود أدمن
function addAdminCode() {
    if (!isOwner) return;
    
    const newCode = document.getElementById('newAdminCode').value.trim();
    const newName = document.getElementById('newAdminName').value.trim();
    
    if (!newCode || !newName) {
        showNotification('يرجى إدخال الكود والاسم!', 'error');
        return;
    }
    
    if (adminCodes[newCode]) {
        showNotification('هذا الكود موجود بالفعل!', 'error');
        return;
    }
    
    adminCodes[newCode] = { 
        name: newName, 
        used: false, 
        isOwner: false 
    };
    
    addInfoLog(`أضاف كود أدمن جديد: "${newCode}" للمستخدم "${newName}"`, currentUser);
    saveDataToFirebase();
    
    document.getElementById('newAdminCode').value = '';
    document.getElementById('newAdminName').value = '';
    displayAdminCodes();
    
    showNotification('تم إضافة الكود بنجاح!', 'success');
    sounds.click();
}

// حذف كود أدمن
function deleteAdminCode(code) {
    if (!isOwner) return;
    
    if (confirm(`هل أنت متأكد من حذف كود "${code}"؟`)) {
        const adminData = adminCodes[code];
        
        addInfoLog(`حذف كود أدمن: "${code}" للمستخدم "${adminData.name}"`, currentUser);
        
        delete adminCodes[code];
        saveDataToFirebase();
        displayAdminCodes();
        
        showNotification('تم حذف الكود بنجاح!', 'success');
        sounds.click();
    }
}

// عرض أكواد الأدمن
function displayAdminCodes() {
    const codesDisplay = document.getElementById('codesDisplay');
    if (!codesDisplay) return;
    
    codesDisplay.innerHTML = '';
    
    for (let code in adminCodes) {
        const adminData = adminCodes[code];
        const status = adminData.used ? 'مستخدم' : 'متاح';
        const statusColor = adminData.used ? '#ff6666' : '#66ff66';
        
        const codeItem = document.createElement('div');
        codeItem.className = 'code-item';
        
        const displayCode = codesVisible ? code : '●'.repeat(code.length);
        
        codeItem.innerHTML = `
            <span class="${codesVisible ? '' : 'code-hidden'}">${displayCode} - ${adminData.name} ${adminData.isOwner ? '<span class="badge owner">👑 مالك</span>' : ''}</span>
            <div>
                <span style="color: ${statusColor}">${status}</span>
                <button class="btn danger small" onclick="deleteAdminCode('${code}')" style="margin-right: 10px;">حذف</button>
            </div>
        `;
        codesDisplay.appendChild(codeItem);
    }
}

// تبديل رؤية الأكواد
function toggleCodesVisibility() {
    codesVisible = !codesVisible;
    const icon = document.getElementById('codesVisibilityIcon');
    const text = document.getElementById('codesVisibilityText');
    
    if (codesVisible) {
        icon.className = 'fas fa-eye';
        text.textContent = 'إخفاء الأكواد';
    } else {
        icon.className = 'fas fa-eye-slash';
        text.textContent = 'إظهار الأكواد';
    }
    
    displayAdminCodes();
}

// مسح السجل
function clearLogs() {
    if (confirm('هل أنت متأكد من مسح جميع السجلات؟')) {
        infoLog = [];
        database.ref('infoLog').set([]).then(() => {
            showNotification('تم مسح السجل بنجاح!', 'success');
            updateInfoLogDisplay();
        });
    }
}

// تصدير السجل
function exportLogs() {
    const logData = infoLog.map(log => 
        `${log.time} - ${log.user}: ${log.action}`
    ).join('\n');
    
    const blob = new Blob([logData], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gang-war-logs-${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    
    showNotification('تم تصدير السجل بنجاح!', 'success');
}

// تحميل محرر معلومات التطبيق
function loadAppInfoEditor() {
    const editor = document.getElementById('appInfoEditor');
    if (editor && appInfo.content) {
        editor.value = appInfo.content;
    }
}

// إغلاق النافذة المنبثقة عند النقر خارجها
document.addEventListener('DOMContentLoaded', function() {
    const gangModal = document.getElementById('gangModal');
    if (gangModal) {
        gangModal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeGangModal();
            }
        });
    }
    
    // تحميل محرر معلومات التطبيق عند تحميل الصفحة
    setTimeout(loadAppInfoEditor, 1000);
});

// تهيئة التطبيق عند تحميل الصفحة
window.addEventListener('load', function() {
    console.log('تم تحميل الصفحة، جاري تهيئة التطبيق...');
    
    // إضافة مستمعي الأحداث للوحة المفاتيح
    document.addEventListener('keydown', function(e) {
        // ESC لإغلاق النوافذ المنبثقة
        if (e.key === 'Escape') {
            closeGangModal();
        }
    });
    
    // إضافة مستمع الأحداث لإخفاء القائمة الجانبية عند النقر خارجها
    document.addEventListener('click', hideSidebarOnClickOutside);
});
