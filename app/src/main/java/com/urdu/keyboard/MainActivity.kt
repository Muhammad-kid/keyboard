package com.urdu.keyboard

import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.view.inputmethod.InputMethodManager
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.urdu.keyboard.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityMainBinding
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupUI()
        checkKeyboardStatus()
    }
    
    private fun setupUI() {
        binding.btnEnableKeyboard.setOnClickListener {
            openInputMethodSettings()
        }
        
        binding.btnSetDefault.setOnClickListener {
            openInputMethodPicker()
        }
        
        binding.btnSettings.setOnClickListener {
            startActivity(Intent(this, SettingsActivity::class.java))
        }
    }
    
    private fun checkKeyboardStatus() {
        val isEnabled = isKeyboardEnabled()
        val isSelected = isKeyboardSelected()
        
        updateKeyboardStatusUI(isEnabled, isSelected)
    }
    
    private fun updateKeyboardStatusUI(isEnabled: Boolean, isSelected: Boolean) {
        binding.tvKeyboardStatus.text = when {
            !isEnabled -> "Keyboard not enabled"
            !isSelected -> "Keyboard enabled but not selected as default"
            else -> "Keyboard is active and ready to use!"
        }
        
        binding.tvKeyboardStatus.setTextColor(
            ContextCompat.getColor(
                this, 
                if (isEnabled && isSelected) R.color.color_green else R.color.color_red
            )
        )
        
        binding.btnEnableKeyboard.isEnabled = !isEnabled
        binding.btnSetDefault.isEnabled = isEnabled && !isSelected
    }
    
    private fun isKeyboardEnabled(): Boolean {
        val inputMethodManager = getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager
        val enabledInputMethods = inputMethodManager.enabledInputMethodList
        
        return enabledInputMethods.any { 
            it.packageName == packageName 
        }
    }
    
    private fun isKeyboardSelected(): Boolean {
        val inputMethodManager = getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager
        val currentInputMethod = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.DEFAULT_INPUT_METHOD
        )
        
        return currentInputMethod?.contains(packageName) == true
    }
    
    private fun openInputMethodSettings() {
        val intent = Intent(Settings.ACTION_INPUT_METHOD_SETTINGS)
        startActivity(intent)
    }
    
    private fun openInputMethodPicker() {
        val inputMethodManager = getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager
        inputMethodManager.showInputMethodPicker()
    }
    
    override fun onResume() {
        super.onResume()
        checkKeyboardStatus()
    }
}