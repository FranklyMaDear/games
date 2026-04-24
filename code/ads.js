// ============================================
// ΑΡΧΕΙΟ ΔΙΑΦΗΜΙΣΕΩΝ - CRACK THE CODE
// Ονομασία: ads.js
// Τοποθετήστε το στον ίδιο φάκελο με το index.html
// ============================================

(function() {
    'use strict';
    
    // Το script της διαφήμισης φορτώνεται δυναμικά
    const adScript = document.createElement('script');
    adScript.src = 'https://al5sm.com/tag.min.js';
    adScript.setAttribute('data-zone', '10416274');
    adScript.async = true;
    adScript.setAttribute('data-cfasync', 'false');
    document.body.appendChild(adScript);
    
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
                // Γράφουμε HTML που φορτώνει το διαφημιστικό script
                adWindow.document.write('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Διαφήμιση</title><style>body{margin:0;background:#111;display:flex;justify-content:center;align-items:center;min-height:100vh;font-family:Arial,sans-serif;color:#fff;}div{text-align:center;font-size:16px;}</style></head><body><div>📢 Φόρτωση...</div><script src="https://al5sm.com/tag.min.js" data-zone="10416274" async data-cfasync="false"><\/script></body></html>');
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
