#include "Songs.h"
#include "Config.h"

// Nokia "Grande Valse" — connect/disconnect jingle
// Frequencies in Hz, durations in note type (8 = eighth, 4 = quarter, 2 = half)
static const int NOKIA_MELODY[] = {
    659, 587, 370, 415,
    554, 494, 294, 330,
    494, 440, 277, 330,
    440
};

static const int NOKIA_DURATIONS[] = {
    8, 8, 4, 4,
    8, 8, 4, 4,
    8, 8, 4, 4,
    2
};

static const int NOKIA_LEN = sizeof(NOKIA_DURATIONS) / sizeof(NOKIA_DURATIONS[0]);

void playNokiaSong() {
    for (int note = 0; note < NOKIA_LEN; note++) {
        int duration = 1000 / NOKIA_DURATIONS[note];
        tone(BUZZER_PIN, NOKIA_MELODY[note], duration);
        delay((int)(duration * 1.30));
        noTone(BUZZER_PIN);
    }
}
