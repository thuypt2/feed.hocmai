/**
 * HOCMAI Feed API — Google Apps Script
 * --------------------------------------------------
 * Copy TOÀN BỘ nội dung file này vào Script Editor,
 * sau đó Deploy lại bản mới.
 *
 * Cách deploy:
 *   1. Mở Apps Script project
 *   2. Dán đè toàn bộ code này
 *   3. Nhấn "Deploy" > "New deployment"
 *   4. Type: Web app
 *   5. Execute as: Me
 *   6. Who has access: Anyone
 *   7. Deploy > Copy URL mới
 *
 * Các sheet được đọc:
 *   Ban_tin  — A:Ngày đăng, C:Tiêu đề, D:Nội dung, I:Kỳ thi, J:Giai đoạn, L:Mức độ
 *   Lich_hoc — toàn bộ cột
 *   So_tay   — toàn bộ cột
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

function readSheet(sheetName) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(sheetName);
  if (!sheet) return [];

  var lastRow = sheet.getLastRow();
  var lastCol = sheet.getLastColumn();
  if (lastRow < 1 || lastCol < 1) return [];

  var raw = sheet.getRange(1, 1, lastRow, lastCol).getValues();

  var result = [];
  var headers = raw[0];

  // Dong 0: copy header de dashboard.js skip
  var headerObj = {};
  for (var c = 0; c < headers.length; c++) {
    headerObj[String(headers[c]).trim()] = String(headers[c]).trim();
  }
  result.push(headerObj);

  for (var i = 1; i < raw.length; i++) {
    var row = raw[i];
    var isEmpty = true;
    for (var c = 0; c < row.length; c++) {
      if (row[c] !== '' && row[c] !== null && row[c] !== undefined) {
        isEmpty = false;
        break;
      }
    }
    if (isEmpty) continue;

    var obj = {};
    for (var c = 0; c < headers.length; c++) {
      var key = String(headers[c]).trim();
      obj[key] = row[c];
    }
    result.push(obj);
  }

  return result;
}
