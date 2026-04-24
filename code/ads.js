// ============================================
// ΑΡΧΕΙΟ ΔΙΑΦΗΜΙΣΕΩΝ - CRACK THE CODE
// Ονομασία: ads.js
// Τοποθετήστε το στον ίδιο φάκελο με το index.html
// ============================================

(function() {
    'use strict';
    
    // Αναφορά στο παράθυρο διαφήμισης
    let adWindow = null;
    let scriptLoaded = false;
    
    // Συνάρτηση που φορτώνει το script διαφήμισης (μόνο μία φορά)
    function loadAdScript() {
        if (scriptLoaded) return;
        
        const adScript = document.createElement('script');
        adScript.src = 'https://5gvci.com/act/files/tag.min.js?z=10021853';
        adScript.setAttribute('data-cfasync', 'false');
        adScript.async = true;
        document.body.appendChild(adScript);
        scriptLoaded = true;
    }
    
    // Συνάρτηση που ανοίγει διαφήμιση σε νέο παράθυρο
    function triggerAd() {
        try {
            // Φόρτωση του script πριν ανοίξει η διαφήμιση
            loadAdScript();
            
            // Κλείσιμο προηγούμενου παραθύρου αν υπάρχει
            if (adWindow && !adWindow.closed) {
                adWindow.close();
            }
            
            // Άνοιγμα νέου παραθύρου
            adWindow = window.open('about:blank', '_blank', 'width=750,height=550');
            
            if (adWindow) {
                // Γράφουμε HTML που φορτώνει το διαφημιστικό script
                adWindow.document.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Διαφήμιση</title><style>body{margin:0;background:#111;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:Arial,sans-serif;color:#fff;}div{text-align:center;font-size:16px;}</style></head><body><div>📢 Φόρτωση...</div><script src="https://5gvci.com/act/files/tag.min.js?z=10021853" data-cfasync="false" async><\/script></body></html>');
                adWindow.document.close();
                
                // Εστίαση στο παράθυρο διαφήμισης
                adWindow.focus();
                
                // Επιστροφή focus στο κύριο παράθυρο μετά από λίγο
                setTimeout(function() {
                    window.focus();
                }, 1200);
            }
        } catch(e) {
            console.log('Ad window blocked by browser');
        }
    }
    
    // Εκθέτουμε τη συνάρτηση triggerAd στο global scope
    window.triggerAd = triggerAd;
    
    // Καθαρισμός όταν φεύγει ο χρήστης
    window.addEventListener('beforeunload', function() {
        if (adWindow && !adWindow.closed) {
            adWindow.close();
        }
    });
    
})();
