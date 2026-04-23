package com.shiba.approver

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.shiba.approver.databinding.ActivityMemoryListBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MemoryListActivity : BaseActivity() {

    override val navItemId = R.id.nav_memory

    private lateinit var binding: ActivityMemoryListBinding
    private val notes = mutableListOf<String>()
    private lateinit var adapter: NoteAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMemoryListBinding.inflate(layoutInflater)
        setContentView(binding.root)

        adapter = NoteAdapter(notes) { noteName ->
            val intent = Intent(this, MemoryNoteActivity::class.java)
            intent.putExtra("note_name", noteName)
            startActivity(intent)
        }
        binding.rvNotes.layoutManager = LinearLayoutManager(this)
        binding.rvNotes.adapter = adapter

        binding.btnRefresh.setOnClickListener { loadNotes() }

        setupBottomNav()
        loadNotes()
    }

    private fun loadNotes() {
        binding.progressBar.visibility = View.VISIBLE
        binding.tvEmpty.visibility = View.GONE
        lifecycleScope.launch {
            val result = withContext(Dispatchers.IO) {
                ApiClient.fetchVaultList(this@MemoryListActivity)
            }
            binding.progressBar.visibility = View.GONE
            if (result.isEmpty()) {
                binding.tvEmpty.visibility = View.VISIBLE
                Toast.makeText(this@MemoryListActivity, "Could not load notes", Toast.LENGTH_SHORT).show()
            } else {
                notes.clear()
                notes.addAll(result)
                adapter.notifyDataSetChanged()
            }
        }
    }
}
