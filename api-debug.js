/**
 * DEBUG VERSION — chạy 1 lần để kiểm tra, xong quay lại api.js
 */
function doGet(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var output = {};

  // 1. Spreadsheet info
  output._spreadsheet = {
    name: ss.getName(),
    id: ss.getId(),
    url: ss.getUrl()
  };

  // 2. List all sheets
  output._sheets = [];
  var sheets = ss.getSheets();
  for (var i = 0; i < sheets.length; i++) {
    var s = sheets[i];
    output._sheets.push({
      name: s.getName(),
      lastRow: s.getLastRow(),
      lastCol: s.getLastColumn()
    });
  }

  // 3. Raw dump Ban_tin — first 3 rows, all columns
  output._Ban_tin_raw = [];
  var bt = ss.getSheetByName('Ban_tin');
  if (bt) {
    var lr = Math.min(bt.getLastRow(), 4);
    var lc = bt.getLastColumn();
    var raw = bt.getRange(1, 1, lr, lc).getValues();
    for (var r = 0; r < raw.length; r++) {
      var rowData = [];
      for (var c = 0; c < raw[r].length; c++) {
        var val = raw[r][c];
        rowData.push({
          col: c + 1,
          colLetter: columnToLetter(c + 1),
          value_type: typeof val,
          value: (typeof val === 'string') ? truncate(val, 200) : val
        });
      }
      output._Ban_tin_raw.push({ row: r + 1, cells: rowData });
    }
  } else {
    output._Ban_tin_raw = 'SHEET NOT FOUND';
  }

  // 4. Also try to run the actual readBanTin() from api.js logic
  output._Ban_tin_test = testReadBanTin(ss);

  return ContentService
    .createTextOutput(JSON.stringify(output, null, 2))
    .setMimeType(ContentService.MimeType.JSON);
}

function testReadBanTin(ss) {
  var sheet = ss.getSheetByName('Ban_tin');
  if (!sheet) return 'NO Ban_tin SHEET';
  var lr = sheet.getLastRow();
  var lc = sheet.getLastColumn();
  var values = sheet.getRange(1, 1, lr, lc).getValues();
  return {
    lastRow: lr,
    lastCol: lc,
    headerRow: values[0].map(function(v, i) { return {col: i+1, val: truncate(String(v), 100)}; }),
    dataRows: lr > 1 ? lr - 1 : 0
  };
}

function columnToLetter(col) {
  var letter = '';
  while (col > 0) {
    var rem = (col - 1) % 26;
    letter = String.fromCharCode(65 + rem) + letter;
    col = Math.floor((col - 1) / 26);
  }
  return letter;
}

function truncate(s, n) {
  if (!s) return '';
  s = String(s);
  return s.length > n ? s.substring(0, n) + '...' : s;
}
