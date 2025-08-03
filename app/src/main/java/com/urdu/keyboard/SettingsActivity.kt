package com.urdu.keyboard

import android.app.Dialog
import android.content.Context
import android.content.SharedPreferences
import android.graphics.Color
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.SeekBar
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.urdu.keyboard.databinding.ActivitySettingsBinding

class SettingsActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivitySettingsBinding
    private lateinit var preferences: SharedPreferences
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        preferences = getSharedPreferences("keyboard_prefs", Context.MODE_PRIVATE)
        
        setupActionBar()
        setupSettings()
        loadSettings()
    }
    
    private fun setupActionBar() {
        supportActionBar?.setDisplayHomeAsUpEnabled(true)
        supportActionBar?.title = getString(R.string.settings_title)
    }
    
    private fun setupSettings() {
        // Color customization
        binding.layoutKeyboardColor.setOnClickListener {
            showColorPickerDialog()
        }
        
        // Vibration setting
        binding.switchVibration.setOnCheckedChangeListener { _, isChecked ->
            preferences.edit().putBoolean("vibration", isChecked).apply()
        }
        
        // Sound setting
        binding.switchSound.setOnCheckedChangeListener { _, isChecked ->
            preferences.edit().putBoolean("key_sound", isChecked).apply()
        }
        
        // Reset to default
        binding.btnResetDefault.setOnClickListener {
            resetToDefaults()
        }
        
        updateColorPreview()
    }
    
    private fun loadSettings() {
        binding.switchVibration.isChecked = preferences.getBoolean("vibration", true)
        binding.switchSound.isChecked = preferences.getBoolean("key_sound", true)
    }
    
    private fun showColorPickerDialog() {
        val dialog = Dialog(this)
        dialog.setContentView(R.layout.dialog_color_picker)
        dialog.window?.setLayout(
            (resources.displayMetrics.widthPixels * 0.9).toInt(),
            (resources.displayMetrics.heightPixels * 0.7).toInt()
        )
        
        setupColorPickerDialog(dialog)
        dialog.show()
    }
    
    private fun setupColorPickerDialog(dialog: Dialog) {
        val predefinedColors = listOf(
            R.color.color_blue, R.color.color_green, R.color.color_red,
            R.color.color_orange, R.color.color_purple, R.color.color_teal,
            R.color.color_indigo, R.color.color_pink, R.color.color_brown,
            R.color.color_grey, R.color.color_dark_blue, R.color.color_dark_green
        )
        
        val colorButtons = listOf(
            dialog.findViewById<Button>(R.id.color_1),
            dialog.findViewById<Button>(R.id.color_2),
            dialog.findViewById<Button>(R.id.color_3),
            dialog.findViewById<Button>(R.id.color_4),
            dialog.findViewById<Button>(R.id.color_5),
            dialog.findViewById<Button>(R.id.color_6),
            dialog.findViewById<Button>(R.id.color_7),
            dialog.findViewById<Button>(R.id.color_8),
            dialog.findViewById<Button>(R.id.color_9),
            dialog.findViewById<Button>(R.id.color_10),
            dialog.findViewById<Button>(R.id.color_11),
            dialog.findViewById<Button>(R.id.color_12)
        )
        
        // Setup predefined color buttons
        colorButtons.forEachIndexed { index, button ->
            if (index < predefinedColors.size) {
                val color = ContextCompat.getColor(this, predefinedColors[index])
                button.setBackgroundColor(color)
                button.setOnClickListener {
                    saveSelectedColor(color)
                    updateColorPreview()
                    dialog.dismiss()
                }
            }
        }
        
        // Setup custom color picker with RGB sliders
        val redSeekBar = dialog.findViewById<SeekBar>(R.id.seekbar_red)
        val greenSeekBar = dialog.findViewById<SeekBar>(R.id.seekbar_green)
        val blueSeekBar = dialog.findViewById<SeekBar>(R.id.seekbar_blue)
        val colorPreview = dialog.findViewById<View>(R.id.color_preview)
        
        var red = 128
        var green = 128
        var blue = 128
        
        val updatePreview = {
            val color = Color.rgb(red, green, blue)
            colorPreview.setBackgroundColor(color)
        }
        
        redSeekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                red = progress
                updatePreview()
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
        })
        
        greenSeekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                green = progress
                updatePreview()
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
        })
        
        blueSeekBar.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                blue = progress
                updatePreview()
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
        })
        
        updatePreview()
        
        // OK and Cancel buttons
        dialog.findViewById<Button>(R.id.btn_ok).setOnClickListener {
            val customColor = Color.rgb(red, green, blue)
            saveSelectedColor(customColor)
            updateColorPreview()
            dialog.dismiss()
        }
        
        dialog.findViewById<Button>(R.id.btn_cancel).setOnClickListener {
            dialog.dismiss()
        }
        
        dialog.findViewById<Button>(R.id.btn_reset).setOnClickListener {
            preferences.edit().remove("keyboard_color").apply()
            updateColorPreview()
            dialog.dismiss()
        }
    }
    
    private fun saveSelectedColor(color: Int) {
        preferences.edit().putInt("keyboard_color", color).apply()
    }
    
    private fun updateColorPreview() {
        val savedColor = preferences.getInt("keyboard_color", 
            ContextCompat.getColor(this, R.color.keyboard_background_default))
        binding.colorPreview.setBackgroundColor(savedColor)
    }
    
    private fun resetToDefaults() {
        preferences.edit().clear().apply()
        
        // Reset to default values
        binding.switchVibration.isChecked = true
        binding.switchSound.isChecked = true
        updateColorPreview()
    }
    
    override fun onSupportNavigateUp(): Boolean {
        onBackPressed()
        return true
    }
}