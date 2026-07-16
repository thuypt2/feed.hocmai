/**
 * HOCMAI Feed API — Google Apps Script
 * Deploy: Publish > Deploy as web app > Execute as "Me" > Who has access "Anyone"
 *
 * Sheets được đọc:
 *   Ban_tin  — cột A:Ngày đăng, C:Tiêu đề, D:Nội dung, I:Kỳ thi, J:Giai đoạn, L:Mức độ
 *   Lich_hoc — toàn bộ cột (tối đa 33 cột)
 *   So_tay   — cột Link (có dấu cách đầu dòng vẫn lấy được)
 *
 * Copy toàn bộ nội dung này vào Script Editor > Dán đè > Lưu > Deploy bản mới.
 */

function doGet(e) {
  var output = {};
  output.Ban_tin  = readSheet('Ban_tin');
  output.Lich_hoc = readSheet('Lich_hoc');
  output.So_tay   = readSheet('So_tay');
  output._index   = readSheet('_index');

  return ContentService
    .createTextOutput(JSON.stringify(output))
    .setMimeType(ContentService.MimeType.JSON);
}

// ── Đọc 1 sheet, trả về mảng object (row[0] = header, row[1..] = data) ──
function readSheet(sheetName) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(sheetName);
  if (!sheet) return [];

  var lastRow = sheet.getLastRow();
  if (lastRow < 1) return [];

  // ── Mỗi sheet có số cột khác nhau ──
  var lastCol, raw;

  if (sheetName === 'Ban_tin') {
    // Đọc A → L (cột 1 → 12)
    lastCol = 12;
    raw = sheet.getRange(1, 1, lastRow, lastCol).getValues();

  } else if (sheetName === 'Lich_hoc') {
    lastCol = sheet.getLastColumn();
    if (lastCol < 1) return [];
    raw = sheet.getRange(1, 1, lastRow, lastCol).getValues();

  } else if (sheetName === 'So_tay') {
    lastCol = sheet.getLastColumn();
    if (lastCol < 1) return [];
    raw = sheet.getRange(1, 1, lastRow, lastCol).getValues();

  } else {
    lastCol = sheet.getLastColumn();
    if (lastCol < 1) return [];
    raw = sheet.getRange(1, 1, lastRow, lastCol).getValues();
  }

  var headers = raw[0];             // hàng đầu = tên cột
  var result = [toObj(headers)];    // dòng 0 copy header để dashboard skip

  for (var i = 1; i < raw.length; i++) {
    var row = raw[i];
    // Bỏ dòng trống hoàn toàn
    if (row.every(function(cell) { return !cell; })) continue;
    result.push(toObj(row));
  }

  return result;
}

// ── Biến mảng [val, val, ...] thành object {header: val, ...} ──
function toObj(arr) {
  var obj = {};
  for (var i = 0; i < arr.length; i++) {
    var key = String(i + 1);      // fallback key là số cột
    obj[key] = arr[i];
  }
  return obj;
}
