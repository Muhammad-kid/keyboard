package com.urdu.keyboard

import android.content.Context
import android.content.SharedPreferences
import android.inputmethodservice.InputMethodService
import android.media.AudioManager
import android.os.Vibrator
import android.view.View
import android.view.inputmethod.EditorInfo
import android.view.inputmethod.InputConnection
import android.widget.Button

class UrduKeyboardService : InputMethodService() {
    
    private lateinit var keyboardView: View
    private lateinit var preferences: SharedPreferences
    private lateinit var vibrator: Vibrator
    private lateinit var audioManager: AudioManager
    
    private var currentKeyboardMode = KeyboardMode.URDU
    private var isShiftPressed = false
    private var isNumberMode = false
    
    enum class KeyboardMode {
        URDU, ENGLISH, EMOJI
    }
    
    override fun onCreateInputView(): View {
        preferences = getSharedPreferences("keyboard_prefs", Context.MODE_PRIVATE)
        vibrator = getSystemService(Context.VIBRATOR_SERVICE) as Vibrator
        audioManager = getSystemService(Context.AUDIO_SERVICE) as AudioManager
        
        keyboardView = when (currentKeyboardMode) {
            KeyboardMode.URDU -> layoutInflater.inflate(R.layout.keyboard_view, null)
            KeyboardMode.ENGLISH -> layoutInflater.inflate(R.layout.english_keyboard_view, null)
            KeyboardMode.EMOJI -> layoutInflater.inflate(R.layout.emoji_keyboard_view, null)
        }
        
        setupKeyboardButtons(keyboardView)
        applyCustomColors()
        
        return keyboardView
    }
    
    private fun setupKeyboardButtons(view: View) {
        when (currentKeyboardMode) {
            KeyboardMode.URDU -> setupUrduKeyboard(view)
            KeyboardMode.ENGLISH -> setupEnglishKeyboard(view)
            KeyboardMode.EMOJI -> setupEmojiKeyboard(view)
        }
    }
    
    private fun setupUrduKeyboard(view: View) {
        // Number keys
        view.findViewById<Button>(R.id.key_1)?.setOnClickListener { onKeyPressed("1") }
        view.findViewById<Button>(R.id.key_2)?.setOnClickListener { onKeyPressed("2") }
        view.findViewById<Button>(R.id.key_3)?.setOnClickListener { onKeyPressed("3") }
        view.findViewById<Button>(R.id.key_4)?.setOnClickListener { onKeyPressed("4") }
        view.findViewById<Button>(R.id.key_5)?.setOnClickListener { onKeyPressed("5") }
        view.findViewById<Button>(R.id.key_6)?.setOnClickListener { onKeyPressed("6") }
        view.findViewById<Button>(R.id.key_7)?.setOnClickListener { onKeyPressed("7") }
        view.findViewById<Button>(R.id.key_8)?.setOnClickListener { onKeyPressed("8") }
        view.findViewById<Button>(R.id.key_9)?.setOnClickListener { onKeyPressed("9") }
        view.findViewById<Button>(R.id.key_0)?.setOnClickListener { onKeyPressed("0") }
        
        // Urdu character keys
        view.findViewById<Button>(R.id.key_urdu_qaf)?.setOnClickListener { onKeyPressed("ق") }
        view.findViewById<Button>(R.id.key_urdu_waao)?.setOnClickListener { onKeyPressed("و") }
        view.findViewById<Button>(R.id.key_urdu_ayn)?.setOnClickListener { onKeyPressed("ع") }
        view.findViewById<Button>(R.id.key_urdu_ray)?.setOnClickListener { onKeyPressed("ر") }
        view.findViewById<Button>(R.id.key_urdu_tay)?.setOnClickListener { onKeyPressed("ت") }
        view.findViewById<Button>(R.id.key_urdu_yay_baree)?.setOnClickListener { onKeyPressed("ے") }
        view.findViewById<Button>(R.id.key_urdu_waao_hamza)?.setOnClickListener { onKeyPressed("ؤ") }
        view.findViewById<Button>(R.id.key_urdu_yay)?.setOnClickListener { onKeyPressed("ی") }
        view.findViewById<Button>(R.id.key_urdu_alif_hamza)?.setOnClickListener { onKeyPressed("ء") }
        view.findViewById<Button>(R.id.key_urdu_pay)?.setOnClickListener { onKeyPressed("پ") }
        
        view.findViewById<Button>(R.id.key_urdu_alif)?.setOnClickListener { onKeyPressed("ا") }
        view.findViewById<Button>(R.id.key_urdu_seen)?.setOnClickListener { onKeyPressed("س") }
        view.findViewById<Button>(R.id.key_urdu_dal)?.setOnClickListener { onKeyPressed("د") }
        view.findViewById<Button>(R.id.key_urdu_fay)?.setOnClickListener { onKeyPressed("ف") }
        view.findViewById<Button>(R.id.key_urdu_gaaf)?.setOnClickListener { onKeyPressed("گ") }
        view.findViewById<Button>(R.id.key_urdu_hay_gol)?.setOnClickListener { onKeyPressed("ہ") }
        view.findViewById<Button>(R.id.key_urdu_jeem)?.setOnClickListener { onKeyPressed("ج") }
        view.findViewById<Button>(R.id.key_urdu_kaaf)?.setOnClickListener { onKeyPressed("ک") }
        view.findViewById<Button>(R.id.key_urdu_laam)?.setOnClickListener { onKeyPressed("ل") }
        
        view.findViewById<Button>(R.id.key_urdu_zay)?.setOnClickListener { onKeyPressed("ز") }
        view.findViewById<Button>(R.id.key_urdu_khay)?.setOnClickListener { onKeyPressed("خ") }
        view.findViewById<Button>(R.id.key_urdu_chay)?.setOnClickListener { onKeyPressed("چ") }
        view.findViewById<Button>(R.id.key_urdu_bay)?.setOnClickListener { onKeyPressed("ب") }
        view.findViewById<Button>(R.id.key_urdu_noon)?.setOnClickListener { onKeyPressed("ن") }
        view.findViewById<Button>(R.id.key_urdu_meem)?.setOnClickListener { onKeyPressed("م") }
        
        // Additional Urdu characters that might be mapped to same keys with shift
        // These can be accessed with shift combinations or long press in future versions
        // ٹ، ڈ، ڑ، ں، ژ، ھ، etc.
        
        // Special keys
        view.findViewById<Button>(R.id.key_space)?.setOnClickListener { onKeyPressed(" ") }
        view.findViewById<Button>(R.id.key_enter)?.setOnClickListener { onEnterPressed() }
        view.findViewById<Button>(R.id.key_backspace)?.setOnClickListener { onBackspacePressed() }
        view.findViewById<Button>(R.id.key_shift)?.setOnClickListener { onShiftPressed() }
        view.findViewById<Button>(R.id.key_language)?.setOnClickListener { switchLanguage() }
        view.findViewById<Button>(R.id.key_emoji)?.setOnClickListener { switchToEmoji() }
        view.findViewById<Button>(R.id.key_numbers)?.setOnClickListener { switchToNumbers() }
    }
    
    private fun setupEnglishKeyboard(view: View) {
        // English character keys
        view.findViewById<Button>(R.id.key_q)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "Q" else "q") }
        view.findViewById<Button>(R.id.key_w)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "W" else "w") }
        view.findViewById<Button>(R.id.key_e)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "E" else "e") }
        view.findViewById<Button>(R.id.key_r)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "R" else "r") }
        view.findViewById<Button>(R.id.key_t)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "T" else "t") }
        view.findViewById<Button>(R.id.key_y)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "Y" else "y") }
        view.findViewById<Button>(R.id.key_u)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "U" else "u") }
        view.findViewById<Button>(R.id.key_i)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "I" else "i") }
        view.findViewById<Button>(R.id.key_o)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "O" else "o") }
        view.findViewById<Button>(R.id.key_p)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "P" else "p") }
        
        view.findViewById<Button>(R.id.key_a)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "A" else "a") }
        view.findViewById<Button>(R.id.key_s)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "S" else "s") }
        view.findViewById<Button>(R.id.key_d)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "D" else "d") }
        view.findViewById<Button>(R.id.key_f)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "F" else "f") }
        view.findViewById<Button>(R.id.key_g)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "G" else "g") }
        view.findViewById<Button>(R.id.key_h)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "H" else "h") }
        view.findViewById<Button>(R.id.key_j)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "J" else "j") }
        view.findViewById<Button>(R.id.key_k)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "K" else "k") }
        view.findViewById<Button>(R.id.key_l)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "L" else "l") }
        
        view.findViewById<Button>(R.id.key_z)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "Z" else "z") }
        view.findViewById<Button>(R.id.key_x)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "X" else "x") }
        view.findViewById<Button>(R.id.key_c)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "C" else "c") }
        view.findViewById<Button>(R.id.key_v)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "V" else "v") }
        view.findViewById<Button>(R.id.key_b)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "B" else "b") }
        view.findViewById<Button>(R.id.key_n)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "N" else "n") }
        view.findViewById<Button>(R.id.key_m)?.setOnClickListener { onKeyPressed(if (isShiftPressed) "M" else "m") }
        
        // Special keys
        view.findViewById<Button>(R.id.key_space_eng)?.setOnClickListener { onKeyPressed(" ") }
        view.findViewById<Button>(R.id.key_enter_eng)?.setOnClickListener { onEnterPressed() }
        view.findViewById<Button>(R.id.key_backspace_eng)?.setOnClickListener { onBackspacePressed() }
        view.findViewById<Button>(R.id.key_shift_eng)?.setOnClickListener { onShiftPressed() }
        view.findViewById<Button>(R.id.key_language_eng)?.setOnClickListener { switchLanguage() }
        view.findViewById<Button>(R.id.key_emoji_eng)?.setOnClickListener { switchToEmoji() }
        view.findViewById<Button>(R.id.key_numbers_eng)?.setOnClickListener { switchToNumbers() }
    }
    
    private fun setupEmojiKeyboard(view: View) {
        val emojiList = listOf(
            "😀", "😂", "😍", "😘", "😊", "😎", "😢", "😭",
            "❤️", "💕", "👍", "👎", "🙏", "👏", "🤝", "✌️",
            "🐱", "🐶", "🌹", "🌟", "☀️", "🌙", "⭐", "🎉"
        )
        
        for (i in 1..24) {
            val buttonId = resources.getIdentifier("emoji_$i", "id", packageName)
            view.findViewById<Button>(buttonId)?.setOnClickListener { 
                onKeyPressed(emojiList[i - 1]) 
            }
        }
        
        view.findViewById<Button>(R.id.key_abc_emoji)?.setOnClickListener { switchLanguage() }
        view.findViewById<Button>(R.id.key_space_emoji)?.setOnClickListener { onKeyPressed(" ") }
        view.findViewById<Button>(R.id.key_backspace_emoji)?.setOnClickListener { onBackspacePressed() }
    }
    
    private fun onKeyPressed(text: String) {
        val inputConnection = currentInputConnection
        inputConnection?.commitText(text, 1)
        
        // Reset shift after character input
        if (isShiftPressed && text.length == 1 && text.isNotEmpty()) {
            isShiftPressed = false
            updateShiftState()
        }
        
        playClickSound()
        vibrate()
    }
    
    private fun onEnterPressed() {
        val inputConnection = currentInputConnection
        val imeOptions = currentInputEditorInfo.imeOptions
        val actionId = imeOptions and EditorInfo.IME_MASK_ACTION
        
        when (actionId) {
            EditorInfo.IME_ACTION_DONE -> inputConnection?.performEditorAction(actionId)
            EditorInfo.IME_ACTION_GO -> inputConnection?.performEditorAction(actionId)
            EditorInfo.IME_ACTION_NEXT -> inputConnection?.performEditorAction(actionId)
            EditorInfo.IME_ACTION_SEARCH -> inputConnection?.performEditorAction(actionId)
            EditorInfo.IME_ACTION_SEND -> inputConnection?.performEditorAction(actionId)
            else -> inputConnection?.commitText("\n", 1)
        }
        
        playClickSound()
        vibrate()
    }
    
    private fun onBackspacePressed() {
        val inputConnection = currentInputConnection
        inputConnection?.deleteSurroundingText(1, 0)
        
        playClickSound()
        vibrate()
    }
    
    private fun onShiftPressed() {
        isShiftPressed = !isShiftPressed
        updateShiftState()
        
        playClickSound()
        vibrate()
    }
    
    private fun updateShiftState() {
        // Update shift button appearance and English key case
        if (currentKeyboardMode == KeyboardMode.ENGLISH) {
            recreateInputView()
        }
    }
    
    private fun switchLanguage() {
        currentKeyboardMode = when (currentKeyboardMode) {
            KeyboardMode.URDU -> KeyboardMode.ENGLISH
            KeyboardMode.ENGLISH -> KeyboardMode.URDU
            KeyboardMode.EMOJI -> KeyboardMode.URDU
        }
        recreateInputView()
    }
    
    private fun switchToEmoji() {
        currentKeyboardMode = KeyboardMode.EMOJI
        recreateInputView()
    }
    
    private fun switchToNumbers() {
        isNumberMode = !isNumberMode
        // For now, just toggle between modes
        recreateInputView()
    }
    
    private fun recreateInputView() {
        setInputView(onCreateInputView())
    }
    
    private fun applyCustomColors() {
        val customColor = preferences.getInt("keyboard_color", -1)
        if (customColor != -1) {
            keyboardView.setBackgroundColor(customColor)
        }
    }
    
    private fun playClickSound() {
        if (preferences.getBoolean("key_sound", true)) {
            audioManager.playSoundEffect(AudioManager.FX_KEYPRESS_STANDARD)
        }
    }
    
    private fun vibrate() {
        if (preferences.getBoolean("vibration", true)) {
            vibrator.vibrate(50)
        }
    }
}