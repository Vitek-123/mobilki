package com.example.test

import android.content.Context
import android.graphics.Color
import android.graphics.Paint
import android.graphics.pdf.PdfDocument
import android.os.Environment
import android.util.Log
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.*

/**
 * Класс для экспорта данных пользователя в PDF
 */
class DataExporter(private val context: Context) {
    
    companion object {
        private const val TAG = "DataExporter"
        private const val PDF_PAGE_WIDTH = 595 // A4 width in points (210mm)
        private const val PDF_PAGE_HEIGHT = 842 // A4 height in points (297mm)
        private const val MARGIN = 50
        private const val LINE_HEIGHT = 20
        private const val TITLE_SIZE = 18f
        private const val HEADING_SIZE = 14f
        private const val TEXT_SIZE = 10f
    }
    
    /**
     * Экспортирует избранное и данные аккаунта в PDF
     */
    suspend fun exportFavoritesToPdf(
        user: UserResponse,
        favorites: List<FavoriteResponse>
    ): Result<File> = withContext(Dispatchers.IO) {
        try {
            Log.d("DataExporter", "Starting PDF export for user: ${user.login}, favorites count: ${favorites.size}")
            val pdfDocument = PdfDocument()
            val pageInfo = PdfDocument.PageInfo.Builder(PDF_PAGE_WIDTH, PDF_PAGE_HEIGHT, 1).create()
            var page = pdfDocument.startPage(pageInfo)
            var canvas = page.canvas
            var yPosition = MARGIN.toFloat()
            
            val paint = Paint().apply {
                isAntiAlias = true
                color = Color.BLACK
            }
            
            val titlePaint = Paint().apply {
                isAntiAlias = true
                color = Color.BLACK
                textSize = TITLE_SIZE
                isFakeBoldText = true
            }
            
            val headingPaint = Paint().apply {
                isAntiAlias = true
                color = Color.BLACK
                textSize = HEADING_SIZE
                isFakeBoldText = true
            }
            
            val textPaint = Paint().apply {
                isAntiAlias = true
                color = Color.BLACK
                textSize = TEXT_SIZE
            }
            
            // Заголовок
            val title = context.getString(R.string.dialog_export_data_title)
            canvas.drawText(title, MARGIN.toFloat(), yPosition, titlePaint)
            yPosition += LINE_HEIGHT * 2
            
            // Дата экспорта
            val dateFormat = SimpleDateFormat("dd.MM.yyyy HH:mm", Locale.getDefault())
            val exportDate = dateFormat.format(Date())
            val dateText = "${context.getString(R.string.export_date)}: $exportDate"
            canvas.drawText(dateText, MARGIN.toFloat(), yPosition, textPaint)
            yPosition += LINE_HEIGHT * 2
            
            // Разделитель
            canvas.drawLine(
                MARGIN.toFloat(),
                yPosition,
                (PDF_PAGE_WIDTH - MARGIN).toFloat(),
                yPosition,
                paint
            )
            yPosition += LINE_HEIGHT
            
            // Данные аккаунта
            canvas.drawText(
                context.getString(R.string.export_account_info),
                MARGIN.toFloat(),
                yPosition,
                headingPaint
            )
            yPosition += LINE_HEIGHT * 1.5f
            
            val loginText = "${context.getString(R.string.export_login)}: ${user.login}"
            canvas.drawText(loginText, MARGIN.toFloat(), yPosition, textPaint)
            yPosition += LINE_HEIGHT
            
            val emailText = "${context.getString(R.string.export_email)}: ${user.email}"
            canvas.drawText(emailText, MARGIN.toFloat(), yPosition, textPaint)
            yPosition += LINE_HEIGHT * 2
            
            // Разделитель
            canvas.drawLine(
                MARGIN.toFloat(),
                yPosition,
                (PDF_PAGE_WIDTH - MARGIN).toFloat(),
                yPosition,
                paint
            )
            yPosition += LINE_HEIGHT
            
            // Избранное
            val favoritesTitle = "${context.getString(R.string.profile_favorites)} (${favorites.size})"
            canvas.drawText(favoritesTitle, MARGIN.toFloat(), yPosition, headingPaint)
            yPosition += LINE_HEIGHT * 1.5f
            
            if (favorites.isEmpty()) {
                val emptyText = context.getString(R.string.export_no_favorites)
                canvas.drawText(emptyText, MARGIN.toFloat(), yPosition, textPaint)
                yPosition += LINE_HEIGHT
            } else {
                favorites.forEachIndexed { index, favorite ->
                    try {
                        // Проверяем, нужна ли новая страница
                        if (yPosition > PDF_PAGE_HEIGHT - MARGIN - 100) {
                            pdfDocument.finishPage(page)
                            val newPageInfo = PdfDocument.PageInfo.Builder(PDF_PAGE_WIDTH, PDF_PAGE_HEIGHT, pdfDocument.pages.size + 1).create()
                            page = pdfDocument.startPage(newPageInfo)
                            canvas = page.canvas
                            yPosition = MARGIN.toFloat()
                        }
                        
                        // Номер товара
                        val itemNumber = "${index + 1}. ${favorite.product.product.title ?: context.getString(R.string.product_name_not_available)}"
                        val boldPaint = Paint(textPaint).apply { isFakeBoldText = true }
                        canvas.drawText(itemNumber, MARGIN.toFloat(), yPosition, boldPaint)
                        yPosition += LINE_HEIGHT
                    
                    // Бренд и модель
                    val brandModel = buildString {
                        if (!favorite.product.product.brand.isNullOrEmpty()) {
                            append("${context.getString(R.string.export_brand)}: ${favorite.product.product.brand}")
                        }
                        if (!favorite.product.product.model.isNullOrEmpty()) {
                            if (isNotEmpty()) append(" | ")
                            append("${context.getString(R.string.export_model)}: ${favorite.product.product.model}")
                        }
                    }
                    if (brandModel.isNotEmpty()) {
                        canvas.drawText(brandModel, (MARGIN + 20).toFloat(), yPosition, textPaint)
                        yPosition += LINE_HEIGHT
                    }
                    
                    // Цены
                    val priceText = buildString {
                        val minPrice = favorite.product.min_price
                        val maxPrice = favorite.product.max_price
                        if (minPrice != null && maxPrice != null) {
                            if (minPrice == maxPrice) {
                                append("${context.getString(R.string.export_price)}: ${formatPrice(minPrice)}")
                            } else {
                                append("${context.getString(R.string.export_price)}: ${formatPrice(minPrice)} - ${formatPrice(maxPrice)}")
                            }
                        } else if (minPrice != null) {
                            append("${context.getString(R.string.export_price)}: ${formatPrice(minPrice)}")
                        } else if (maxPrice != null) {
                            append("${context.getString(R.string.export_price)}: ${formatPrice(maxPrice)}")
                        } else if (favorite.product.prices.isNotEmpty()) {
                            // Если min/max не указаны, берем из списка цен
                            val prices = favorite.product.prices.mapNotNull { it.price }
                            if (prices.isNotEmpty()) {
                                val min = prices.minOrNull()
                                val max = prices.maxOrNull()
                                if (min != null && max != null) {
                                    if (min == max) {
                                        append("${context.getString(R.string.export_price)}: ${formatPrice(min)}")
                                    } else {
                                        append("${context.getString(R.string.export_price)}: ${formatPrice(min)} - ${formatPrice(max)}")
                                    }
                                }
                            }
                        }
                    }
                    if (priceText.isNotEmpty()) {
                        canvas.drawText(priceText, (MARGIN + 20).toFloat(), yPosition, textPaint)
                        yPosition += LINE_HEIGHT
                    }
                    
                    // Магазины
                    if (favorite.product.prices.isNotEmpty()) {
                        val shopsText = "${context.getString(R.string.export_shops)}: ${favorite.product.prices.joinToString(", ") { it.shop_name }}"
                        canvas.drawText(shopsText, (MARGIN + 20).toFloat(), yPosition, textPaint)
                        yPosition += LINE_HEIGHT
                    }
                    
                    // Дата добавления
                    val dateFormat = SimpleDateFormat("dd.MM.yyyy", Locale.getDefault())
                    val addedDate = try {
                        val date = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault()).parse(favorite.added_at)
                        if (date != null) dateFormat.format(date) else favorite.added_at
                    } catch (e: Exception) {
                        favorite.added_at
                    }
                    val addedText = "${context.getString(R.string.export_added_date)}: $addedDate"
                    canvas.drawText(addedText, (MARGIN + 20).toFloat(), yPosition, textPaint)
                    yPosition += LINE_HEIGHT
                    
                    // Ссылки на магазины
                    favorite.product.prices.forEach { price ->
                        if (!price.url.isNullOrEmpty()) {
                            val urlText = "${price.shop_name}: ${price.url}"
                            // Обрезаем длинные URL для читаемости
                            val displayUrl = if (urlText.length > 80) urlText.take(80) + "..." else urlText
                            val urlPaint = Paint(textPaint).apply { color = Color.BLUE }
                            canvas.drawText(displayUrl, (MARGIN + 40).toFloat(), yPosition, urlPaint)
                            yPosition += LINE_HEIGHT
                        }
                    }
                    
                    yPosition += LINE_HEIGHT
                    } catch (e: Exception) {
                        Log.e(TAG, "Error processing favorite item ${index + 1}: ${e.message}", e)
                        // Продолжаем обработку остальных товаров
                    }
                }
            }
            
            pdfDocument.finishPage(page)
            
            // Сохраняем файл
            val fileName = "ScanPrice_Export_${SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())}.pdf"
            val documentsDir = context.getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS)
            val file = File(documentsDir, fileName)
            
            val parentFile = file.parentFile
            if (parentFile != null && !parentFile.exists()) {
                parentFile.mkdirs()
            }
            
            FileOutputStream(file).use { outputStream ->
                pdfDocument.writeTo(outputStream)
            }
            
            pdfDocument.close()
            
            Log.d(TAG, "PDF exported successfully: ${file.absolutePath}")
            Result.success(file)
            
        } catch (e: Exception) {
            Log.e(TAG, "Error exporting PDF", e)
            Result.failure(e)
        }
    }
    
    private fun formatPrice(price: Float?): String {
        return if (price != null) {
            CurrencyUtils.formatPrice(context, price)
        } else {
            context.getString(R.string.price_not_available)
        }
    }
}

