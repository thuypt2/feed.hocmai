-- =====================================================
-- Chạy toàn bộ script này trong Supabase SQL Editor:
-- https://xaxohdyscyxbamvtdjzw.supabase.co → SQL Editor → New Query
-- =====================================================

-- 1. Bảng ban_tin (News Feed)
CREATE TABLE IF NOT EXISTS ban_tin (
  id          BIGSERIAL PRIMARY KEY,
  ngay_dang   TIMESTAMPTZ,
  nguoi_dang  TEXT DEFAULT '',
  tieu_de     TEXT,
  noi_dung    TEXT,
  section     TEXT DEFAULT 'Tin mới',
  start_time  TIMESTAMPTZ,
  end_time    TIMESTAMPTZ,
  loai_tb     TEXT DEFAULT '',
  ky_thi      TEXT DEFAULT 'All',
  giai_doan   TEXT DEFAULT '',
  lo_trinh    TEXT DEFAULT 'All',
  muc_do      TEXT DEFAULT 'Cần biết',
  hashtag     TEXT DEFAULT '',
  xuat_ban    BOOLEAN DEFAULT TRUE,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- 2. Bảng lich_hoc (Schedule)
CREATE TABLE IF NOT EXISTS lich_hoc (
  id             BIGSERIAL PRIMARY KEY,
  ten_bai_giang  TEXT,
  ten_gv         TEXT DEFAULT '',
  ngay_live      TIMESTAMPTZ,
  khung_gio      TEXT DEFAULT '',
  ky_thi_lop     TEXT DEFAULT 'All',
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Bảng so_tay (Quick Links)
CREATE TABLE IF NOT EXISTS so_tay (
  id         BIGSERIAL PRIMARY KEY,
  tieu_de    TEXT,
  link       TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Bảng _index (Icon mapping)
CREATE TABLE IF NOT EXISTS _index (
  id        BIGSERIAL PRIMARY KEY,
  loai_tb   TEXT,
  icon      TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- BẬT RLS + Public read access (cho phép frontend đọc)
-- =====================================================
ALTER TABLE ban_tin  ENABLE ROW LEVEL SECURITY;
ALTER TABLE lich_hoc ENABLE ROW LEVEL SECURITY;
ALTER TABLE so_tay  ENABLE ROW LEVEL SECURITY;
ALTER TABLE _index  ENABLE ROW LEVEL SECURITY;

-- Policy: ai cũng đọc được (SELECT)
CREATE POLICY "Public read" ON ban_tin  FOR SELECT USING (true);
CREATE POLICY "Public read" ON lich_hoc FOR SELECT USING (true);
CREATE POLICY "Public read" ON so_tay  FOR SELECT USING (true);
CREATE POLICY "Public read" ON _index  FOR SELECT USING (true);

-- Policy: chỉ service_role được INSERT/UPDATE/DELETE
CREATE POLICY "Service insert" ON ban_tin  FOR INSERT WITH CHECK (true);
CREATE POLICY "Service update" ON ban_tin  FOR UPDATE USING (true);
CREATE POLICY "Service delete" ON ban_tin  FOR DELETE USING (true);

CREATE POLICY "Service insert" ON lich_hoc FOR INSERT WITH CHECK (true);
CREATE POLICY "Service update" ON lich_hoc FOR UPDATE USING (true);
CREATE POLICY "Service delete" ON lich_hoc FOR DELETE USING (true);

CREATE POLICY "Service insert" ON so_tay  FOR INSERT WITH CHECK (true);
CREATE POLICY "Service update" ON so_tay  FOR UPDATE USING (true);
CREATE POLICY "Service delete" ON so_tay  FOR DELETE USING (true);

CREATE POLICY "Service insert" ON _index  FOR INSERT WITH CHECK (true);
CREATE POLICY "Service update" ON _index  FOR UPDATE USING (true);
CREATE POLICY "Service delete" ON _index  FOR DELETE USING (true);
