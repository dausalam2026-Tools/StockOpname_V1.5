package com.gmf.stockopname.data

/** One tool record, exactly as it appears in the Master Tools Database. */
data class Tool(
    val toolNumber: String,
    val partNumber: String,
    val keyNumber: String,
    val serialNumber: String,
    val description: String,
    val manufacture: String,
    val model: String,
    val status: String, // available/calibration/borrowed/quarantined/maintenance/broken/missing
    val store: String,
    val location: String,
    val dueDate: String? = null // kalibrasi berikutnya, format ISO "YYYY-MM-DD"; null = tidak ada data
)

/** Opname (verification) result for one tool: pending / OK / Discrepancy. */
enum class OpnameResult { PENDING, OK, DISCREPANCY }

data class LocationStats(
    val total: Int,
    val checked: Int,
    val ok: Int,
    val discrepancy: Int
) {
    val remaining: Int get() = total - checked
    val isComplete: Boolean get() = total > 0 && checked == total
    val percent: Float get() = if (total == 0) 0f else checked.toFloat() / total
}

data class HistoryEntry(
    val store: String,
    val location: String,
    val finishedAtMillis: Long?,
    val stats: LocationStats,
    val lastActivityMillis: Long? = null
)

val STATUS_LABELS = mapOf(
    "available" to "Available",
    "calibration" to "Kalibrasi",
    "borrowed" to "Dipinjam",
    "quarantined" to "Quarantine",
    "maintenance" to "Maintenance",
    "broken" to "Rusak",
    "missing" to "Hilang"
)

val STORE_LABELS = mapOf(
    "H4" to "Store H4",
    "PC" to "Store PC",
    "ML" to "Store ML",
    "HP" to "Store HP",
    "W1" to "Store W1",
    "W2" to "Store W2",
    "LG" to "Store LG (Landing Gear)"
)

/** Kategori besar Tool Store: tiap grup berisi beberapa kode store dari kolom "Store". */
data class StoreGroup(val title: String, val stores: List<String>)

val GROUP_HANGAR4 = StoreGroup("Tool Store Hangar 4", listOf("H4", "PC", "ML", "HP"))
val GROUP_COMPONENT_WORKSHOP = StoreGroup("Tool Store Component Workshop", listOf("W1", "W2", "LG"))
val STORE_GROUPS = listOf(GROUP_COMPONENT_WORKSHOP, GROUP_HANGAR4)

/** Nama grup untuk satu kode store (null kalau store belum masuk grup mana pun). */
fun groupTitleForStore(storeId: String): String? =
    STORE_GROUPS.firstOrNull { storeId in it.stores }?.title
