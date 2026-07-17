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
 *   Ban_tin  — A:Ngày đăng, C:Tiêu đề, D:Nội dung (rich text → HTML), I:Kỳ thi, J:Giai đoạn, L:Mức độ
 *   Lich_hoc — toàn bộ cột
 *   So_tay   — toàn bộ cột
 */

function doGet(e) {
  var output = {};
  output.Ban_tin  = readBanTin();
  output.Lich_hoc = readSheetPlain('Lich_hoc');
  output.So_tay   = readSheetPlain('So_tay');
  output._index   = readSheetPlain('_index');

  return ContentService
    .createTextOutput(JSON.stringify(output))
    .setMimeType(ContentService.MimeType.JSON);
}

/**
 * Đọc sheet Ban_tin — cột D (Nội dung) và C (Tiêu đề) được convert từ rich text → HTML
 * Các cột khác vẫn đọc dạng plain text.
 */
function readBanTin() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName('Ban_tin');
  if (!sheet) return [];

  var lastRow = sheet.getLastRow();
  var lastCol = sheet.getLastColumn();
  if (lastRow < 2 || lastCol < 1) return [];

  // Đọc toàn bộ plain values
  var values = sheet.getRange(1, 1, lastRow, lastCol).getValues();

  // Tìm dòng header thực sự (skip các dòng trống ở đầu)
  var headerRowIdx = 0;
  while (headerRowIdx < values.length) {
    var row = values[headerRowIdx];
    var nonEmpty = false;
    for (var c = 0; c < row.length; c++) {
      if (row[c] !== '' && row[c] !== null) { nonEmpty = true; break; }
    }
    if (nonEmpty) break;
    headerRowIdx++;
  }
  if (headerRowIdx >= values.length) return []; // All empty

  var headers = values[headerRowIdx];

  // Đọc rich text cho cột C (3) và D (4), offset theo headerRowIdx
  var richColC = sheet.getRange(headerRowIdx + 1, 3, lastRow - headerRowIdx, 1).getRichTextValues();
  var richColD = sheet.getRange(headerRowIdx + 1, 4, lastRow - headerRowIdx, 1).getRichTextValues();

  var result = [];

  // Dòng header (để dashboard skip)
  var headerObj = {};
  for (var c = 0; c < headers.length; c++) {
    var key = String(headers[c]).trim();
    if (!key) key = String(c + 1); // fallback key nếu header rỗng
    headerObj[key] = key;
  }
  result.push(headerObj);

  // Dữ liệu (bắt đầu từ dòng sau header) — dùng values.length để không sót dòng cuối
  for (var i = headerRowIdx + 1; i < values.length; i++) {
    var row = values[i];
    var isEmpty = true;
    for (var c = 0; c < row.length; c++) {
      if (row[c] !== '' && row[c] !== null && row[c] !== undefined) {
        isEmpty = false;
        break;
      }
    }
    if (isEmpty) continue;

    var obj = {};
    var richRowIdx = i - headerRowIdx; // richColX[0]=header row, richColX[1]=1st data row, ...
    for (var c = 0; c < headers.length; c++) {
      var key = String(headers[c]).trim();
      if (!key) key = String(c + 1);
      if (c === 2) {
        // Cột C (0-based index 2) = Tiêu đề → rich text
        // Fallback plain value nếu rich text lệch offset
        var rtC = (richRowIdx >= 0 && richRowIdx < richColC.length) ? richColC[richRowIdx][0] : null;
        var htmlC = richTextToHtml(rtC);
        var plainC = row[c] != null ? String(row[c]) : '';
        // Nếu rich text trả về text trùng header (artifact) thì dùng plain
        if (!htmlC || htmlC.replace(/<[^>]*>/g, '').trim() === String(headers[2]).trim()) {
          obj[key] = escapeHtml(plainC);
        } else {
          obj[key] = htmlC;
        }
      } else if (c === 3) {
        // Cột D (0-based index 3) = Nội dung → rich text
        var rtD = (richRowIdx >= 0 && richRowIdx < richColD.length) ? richColD[richRowIdx][0] : null;
        var htmlD = richTextToHtml(rtD);
        var plainD = row[c] != null ? String(row[c]) : '';
        if (!htmlD || htmlD.replace(/<[^>]*>/g, '').trim() === String(headers[3]).trim()) {
          obj[key] = escapeHtml(plainD);
        } else {
          obj[key] = htmlD;
        }
      } else {
        obj[key] = row[c];
      }
    }
    result.push(obj);
  }

  return result;
}

/**
 * Chuyển 1 ô RichTextValue → HTML string
 * Hỗ trợ: bold, italic, underline, strikethrough, màu chữ, link
 */
function richTextToHtml(rtValue) {
  if (!rtValue) return '';

  var textPlain = rtValue.getText();
  if (!textPlain) return '';

  var runs = rtValue.getRuns();
  if (runs.length === 0) return escapeHtml(textPlain);

  var htmlParts = [];

  for (var r = 0; r < runs.length; r++) {
    var run = runs[r];
    var text = run.getText();
    if (!text) continue;

    var style = run.getTextStyle();
    var linkUrl = run.getLinkUrl();
    var wrapped = escapeHtml(text);

    // Theo thứ tự từ trong ra ngoài
    if (style.isBold())      wrapped = '<b>' + wrapped + '</b>';
    if (style.isItalic())     wrapped = '<i>' + wrapped + '</i>';
    if (style.isUnderline())  wrapped = '<u>' + wrapped + '</u>';
    if (style.isStrikethrough()) wrapped = '<s>' + wrapped + '</s>';

    // Màu chữ (foreground color)
    if (style.getForegroundColor) {
      var fg = style.getForegroundColor();
      if (fg && fg !== '#000000' && fg !== '#000') {
        wrapped = '<span style="color:' + fg + '">' + wrapped + '</span>';
      }
    }

    // Link URL
    if (linkUrl) {
      wrapped = '<a href="' + linkUrl + '" target="_blank" rel="noopener" style="color:#005BAC;word-break:break-all">' + wrapped + '</a>';
    }

    htmlParts.push(wrapped);
  }

  return htmlParts.join('');
}

/**
 * Đọc sheet bình thường (plain text) cho Lich_hoc, So_tay, _index
 */
function readSheetPlain(sheetName) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(sheetName);
  if (!sheet) return [];

  var lastRow = sheet.getLastRow();
  var lastCol = sheet.getLastColumn();
  if (lastRow < 2 || lastCol < 1) return [];

  var raw = sheet.getRange(1, 1, lastRow, lastCol).getValues();

  // Tìm dòng header thực sự (skip các dòng trống ở đầu)
  var headerRowIdx = 0;
  while (headerRowIdx < raw.length) {
    var checkRow = raw[headerRowIdx];
    var nonEmpty = false;
    for (var c = 0; c < checkRow.length; c++) {
      if (checkRow[c] !== '' && checkRow[c] !== null) { nonEmpty = true; break; }
    }
    if (nonEmpty) break;
    headerRowIdx++;
  }
  if (headerRowIdx >= raw.length) return [];

  var headers = raw[headerRowIdx];
  var result = [];

  var headerObj = {};
  for (var c = 0; c < headers.length; c++) {
    var key = String(headers[c]).trim();
    if (!key) key = String(c + 1); // fallback key nếu header rỗng
    headerObj[key] = key;
  }
  result.push(headerObj);

  for (var i = headerRowIdx + 1; i < raw.length; i++) {
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
      if (!key) key = String(c + 1);
      obj[key] = row[c];
    }
    result.push(obj);
  }

  return result;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
