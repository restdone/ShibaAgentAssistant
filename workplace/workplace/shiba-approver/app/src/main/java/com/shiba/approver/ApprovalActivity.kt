package com.shiba.approver

import android.os.Bundle
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.shiba.approver.databinding.ActivityApprovalBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class ApprovalActivity : AppCompatActivity() {

    private lateinit var binding: ActivityApprovalBinding
    private var requestId: String = ""

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityApprovalBinding.inflate(layoutInflater)
        setContentView(binding.root)

        requestId              = intent.getStringExtra("request_id")      ?: ""
        val type               = intent.getStringExtra("request_type")    ?: ""
        val summary            = intent.getStringExtra("request_summary") ?: ""
        val detail             = intent.getStringExtra("request_detail")  ?: ""

        binding.tvType.text    = type.replace("_", " ").replaceFirstChar { it.uppercase() }
        binding.tvSummary.text = summary
        binding.tvDetail.text  = detail

        binding.btnApprove.setOnClickListener { sendDecision(true) }
        binding.btnReject.setOnClickListener  { sendDecision(false) }
    }

    private fun sendDecision(approved: Boolean) {
        binding.btnApprove.isEnabled = false
        binding.btnReject.isEnabled  = false

        lifecycleScope.launch {
            val ok = withContext(Dispatchers.IO) {
                ApiClient.respond(this@ApprovalActivity, requestId, approved)
            }
            if (ok) {
                val msg = if (approved) "Approved" else "Rejected"
                Toast.makeText(this@ApprovalActivity, msg, Toast.LENGTH_SHORT).show()
            } else {
                Toast.makeText(this@ApprovalActivity, "Failed to reach server", Toast.LENGTH_SHORT).show()
            }
            finish()
        }
    }
}
