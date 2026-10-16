package com.gmf.stockopname.ui.screens

import android.Manifest
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.gmf.stockopname.ui.theme.MutedLight
import com.google.accompanist.permissions.ExperimentalPermissionsApi
import com.google.accompanist.permissions.isGranted
import com.google.accompanist.permissions.rememberPermissionState

/** Pop-up kamera untuk membaca satu barcode. [onCode] dipanggil sekali dengan isi barcode yang terbaca. */
@OptIn(ExperimentalPermissionsApi::class)
@Composable
fun BarcodeScanDialog(onCode: (String) -> Unit, onDismiss: () -> Unit) {
    val cameraPermission = rememberPermissionState(Manifest.permission.CAMERA)
    var done by remember { mutableStateOf(false) }

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Card(
            modifier = Modifier.padding(16.dp).fillMaxWidth(),
            shape = RoundedCornerShape(16.dp)
        ) {
            Column(Modifier.padding(16.dp)) {
                Text("Scan Barcode", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                Text("Arahkan kamera ke barcode pada tool.", color = MutedLight, fontSize = 12.sp)
                Spacer(Modifier.height(12.dp))
                Box(
                    Modifier
                        .fillMaxWidth()
                        .height(240.dp)
                        .background(Color(0xFF0A1220), RoundedCornerShape(12.dp)),
                    contentAlignment = Alignment.Center
                ) {
                    if (cameraPermission.status.isGranted) {
                        CameraPreviewWithBarcodeScanner(onDetected = { code ->
                            if (!done) {
                                done = true
                                onCode(code)
                            }
                        })
                        Box(
                            Modifier
                                .size(190.dp, 110.dp)
                                .border(2.5.dp, Color(0xFF4C9BFF), RoundedCornerShape(10.dp))
                        )
                    } else {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("Kamera belum aktif", color = Color.White)
                            Spacer(Modifier.height(10.dp))
                            Button(onClick = { cameraPermission.launchPermissionRequest() }) {
                                Text("Aktifkan Kamera")
                            }
                        }
                    }
                }
                Spacer(Modifier.height(12.dp))
                OutlinedButton(onClick = onDismiss, modifier = Modifier.fillMaxWidth()) { Text("Batal") }
            }
        }
    }
}
