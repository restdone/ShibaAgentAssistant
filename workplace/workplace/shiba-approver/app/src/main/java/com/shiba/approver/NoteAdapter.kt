package com.shiba.approver

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView

class NoteAdapter(
    private val items: List<String>,
    private val onClick: (String) -> Unit,
) : RecyclerView.Adapter<NoteAdapter.VH>() {

    inner class VH(view: View) : RecyclerView.ViewHolder(view) {
        val tv: TextView = view.findViewById(android.R.id.text1)
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val view = LayoutInflater.from(parent.context)
            .inflate(android.R.layout.simple_list_item_1, parent, false)
        return VH(view)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        val name = items[position]
        // Show only the last segment of the path for readability
        holder.tv.text = name.substringAfterLast("/")
        holder.tv.setOnClickListener { onClick(name) }
    }

    override fun getItemCount() = items.size
}
