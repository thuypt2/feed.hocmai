// ══════════════════════════════════════════════════════════
// AUTO-SYNC: Khi tick "Xuất bản" → tự động sync lên Supabase
// ══════════════════════════════════════════════════════════
// Cách cài đặt:
//   1. Mở Google Sheet "Ban_tin"
//   2. Extensions → Apps Script
//   3. Dán code này vào, nhấn 💾 Save
//   4. Chạy createTrigger() một lần để bật onEdit
//   5. Test: sửa 1 ô "Xuất bản" → check bantintopuni.vercel.app
// ══════════════════════════════════════════════════════════

const SYNC_URL = 'https://bantintopuni.vercel.app/api/sync';
const SHEET_NAME = 'Ban_tin';    // Tên sheet chứa dữ liệu
const COL_XUAT_BAN = 14;         // Cột N (index 14 = cột "Xuất bản")

/**
 * Tự động chạy khi bạn sửa bất kỳ ô nào trong sheet.
 */
function onEdit(e) {
  const range = e.range;
  const sheet = range.getSheet();
  
  // Chỉ xử lý sheet Ban_tin
  if (sheet.getName() !== SHEET_NAME) return;
  
  // Chỉ xử lý cột "Xuất bản" (cột N)
  if (range.getColumn() !== COL_XUAT_BAN) return;
  
  const value = range.getValue();
  const row = range.getRow();
  
  // Bỏ qua header row (dòng 1)
  if (row <= 1) return;
  
  // Nếu tick TRUE → gọi sync
  if (value === true || value === 'TRUE' || value === true) {
    callSyncApi(row);
  }
}

/**
 * Gọi Vercel API sync và thông báo kết quả.
 */
function callSyncApi(row) {
  const sheet = SpreadsheetApp.getActiveSheet();
  
  // Lấy tiêu đề bài viết đang xuất bản
  const tieuDe = sheet.getRange(row, 3).getValue() || '(không tiêu đề)';
  
  sheet.toast(`🔄 Đang đồng bộ: "${String(tieuDe).substring(0, 40)}"...`, 'Sync', 30);
  
  const startTime = Date.now();
  
  try {
    const response = UrlFetchApp.fetch(SYNC_URL, {
      muteHttpExceptions: true,
      timeout: 120
    });
    
    const result = JSON.parse(response.getContentText());
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    
    if (result.ok) {
      const msg = `✅ Đồng bộ xong (${elapsed}s): ${result.ban_tin} tin, ${result.lich_hoc} lịch học, ${result.so_tay} sổ tay, ${result._index} icon`;
      sheet.toast(msg, 'Sync thành công', 5);
    } else {
      const errorMsg = (result.messages || [result.error]).filter(Boolean).join('; ');
      sheet.toast(`❌ Lỗi: ${errorMsg}`, 'Sync thất bại', 10);
    }
  } catch (error) {
    sheet.toast(`❌ Lỗi kết nối: ${error.toString().substring(0, 100)}`, 'Sync thất bại', 10);
  }
}

/**
 * Cài đặt trigger onEdit (chạy 1 lần).
 * Vào Run → Run function → createTrigger
 */
function createTrigger() {
  // Xóa trigger cũ nếu có
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(t => {
    if (t.getHandlerFunction() === 'onEdit') {
      ScriptApp.deleteTrigger(t);
    }
  });
  
  // Tạo trigger mới
  ScriptApp.newTrigger('onEdit')
    .forSpreadsheet(SpreadsheetApp.getActiveSpreadsheet())
    .onEdit()
    .create();
  
  SpreadsheetApp.getActiveSheet().toast('✅ onEdit trigger đã được cài đặt!', 'Sync Auto', 5);
}

/**
 * Kiểm tra kết nối API (chạy thử).
 * Vào Run → Run function → testSync
 */
function testSync() {
  callSyncApi(2); // giả sử tick ở dòng 2
}
