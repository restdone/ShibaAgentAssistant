package com.shiba.approver

import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.shiba.approver.databinding.ActivityMemoryNoteBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MemoryNoteActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMemoryNoteBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMemoryNoteBinding.inflate(layoutInflater)
        setContentView(binding.root)

        val noteName = intent.getStringExtra("note_name") ?: return
        supportActionBar?.title = noteName.substringAfterLast("/")

        loadNote(noteName)
    }

    private fun loadNote(noteName: String) {
        binding.progressBar.visibility = View.VISIBLE
        binding.tvContent.visibility = View.GONE
        lifecycleScope.launch {
            val content = withContext(Dispatchers.IO) {
                ApiClient.fetchVaultNote(this@MemoryNoteActivity, noteName)
            }
            binding.progressBar.visibility = View.GONE
            if (content == null) {
                Toast.makeText(this@MemoryNoteActivity, "Could not load note", Toast.LENGTH_SHORT).show()
                finish()
            } else {
                binding.tvContent.visibility = View.VISIBLE
                binding.tvContent.text = content
            }
        }
    }
}
