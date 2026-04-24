// ============================================
// ΑΡΧΕΙΟ ΔΙΑΦΗΜΙΣΕΩΝ - CRACK THE CODE
// Ονομασία: ads.js
// Τοποθετήστε το στον ίδιο φάκελο με το index.html
// ============================================

(function() {
    'use strict';
    
    // Νέο script διαφήμισης με zone 10274195
    (function(s){
        s.dataset.zone = '10274195';
        s.src = 'https://al5sm.com/tag.min.js';
    })([document.documentElement, document.body].filter(Boolean).pop().appendChild(document.createElement('script')));
    
    // Αναφορά στο παράθυρο διαφήμισης
    let adWindow = null;
    
    // Συνάρτηση που ανοίγει διαφήμιση σε νέο παράθυρο
    function triggerAd() {
        try {
            // Κλείσιμο προηγούμενου παραθύρου αν υπάρχει
            if (adWindow && !adWindow.closed) {
                adWindow.close();
            }
            
            // Άνοιγμα νέου παραθύρου
            adWindow = window.open('about:blank', '_blank', 'width=750,height=550');
            
            if (adWindow) {
                // Γράφουμε HTML που φορτώνει το διαφημιστικό script με το νέο zone
                adWindow.document.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Διαφήμιση</title><style>body{margin:0;background:#111;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:Arial,sans-serif;color:#fff;}div{text-align:center;font-size:16px;}</style></head><body><div>📢 Φόρτωση...</div><script>(function(s){s.dataset.zone="10274195";s.src="https://al5sm.com/tag.min.js";})(document.currentScript.parentNode.appendChild(document.createElement("script")))<\/script></body></html>');
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
