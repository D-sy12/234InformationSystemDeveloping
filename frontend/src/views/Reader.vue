<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElDrawer } from 'element-plus'
import api from '@/api'

const route = useRoute()
const router = useRouter()

const book = ref(null)
const loading = ref(true)
const content = ref('')
const pages = ref([])
const currentPage = ref(0)
const toc = ref([])
const showToc = ref(false)
const fontSize = ref(18)
const bodyRef = ref(null)

// 翻页后阅读区自动回到顶部
watch(currentPage, () => {
  nextTick(() => bodyRef.value?.scrollTo({ top: 0 }))
})

const PAGE_SIZE = 1100

const totalPages = computed(() => pages.value.length || 1)
const progressPct = computed(() => totalPages.value ? Math.round((currentPage.value + 1) / totalPages.value * 100) : 0)

const chapterTitle = computed(() => {
  const start = pageStart(currentPage.value)
  let title = ''
  for (const c of toc.value) {
    if (c.offset <= start) title = c.title
    else break
  }
  return title || '正文'
})

function extractChapters(text) {
  const chs = []
  // 回目后必须跟空白或行尾，避免误匹配“第四回中既將…”这类正文
  const reCN = /^(第[一二三四五六七八九十百千零〇两\d]+[回章节卷])(?=[ \t　]|\r?$)[ \t　]*([^\n]{0,60}?)[ \t　\r]*$/gm
  const reEN = /^(CHAPTER|Chapter)\s+([IVXLC\d]+)[.:\s]*([^\n]{0,60})?$/gm
  let m
  while ((m = reCN.exec(text)) !== null) {
    let sub = (m[2] || '').trim()
    if (!sub) {
      // 标题在后续行（中间可能隔着空行和 ---- 分隔线）
      const lines = text.slice(m.index + m[0].length).split('\n').slice(1, 9)
      for (const ln of lines) {
        const t = ln.trim()
        if (!t || /^[-—=*\s]+$/.test(t)) continue // 跳过空行与分隔线
        if (t.length <= 40) sub = t
        break // 遇到正文行（过长）则放弃
      }
    }
    chs.push({ title: (m[1] + (sub ? ' ' + sub : '')).trim(), offset: m.index })
  }
  while ((m = reEN.exec(text)) !== null) {
    chs.push({ title: (m[1] + ' ' + m[2] + (m[3] ? ' ' + m[3].trim() : '')).trim(), offset: m.index })
  }
  chs.sort((a, b) => a.offset - b.offset)
  // 去重同一 offset
  return chs.filter((c, i, arr) => i === 0 || c.offset !== arr[i - 1].offset)
}

function paginate(text) {
  const arr = []
  let i = 0
  while (i < text.length) {
    let end = Math.min(i + PAGE_SIZE, text.length)
    if (end < text.length) {
      const slice = text.slice(i, end)
      let cut = slice.lastIndexOf('\n')
      if (cut > PAGE_SIZE * 0.5) end = i + cut + 1
    }
    arr.push(text.slice(i, end))
    i = end
  }
  return arr
}

function pageStart(p) {
  let s = 0
  for (let i = 0; i < p; i++) s += pages.value[i].length
  return s
}

function findPageByOffset(offset) {
  let cum = 0
  for (let p = 0; p < pages.value.length; p++) {
    const len = pages.value[p].length
    if (offset >= cum && offset < cum + len) return p
    cum += len
  }
  return 0
}

function saveProgress() {
  if (!book.value) return
  localStorage.setItem(`reader_progress_${book.value.id}`, String(currentPage.value))
}

function loadProgress() {
  if (!book.value) return 0
  const s = localStorage.getItem(`reader_progress_${book.value.id}`)
  const n = s ? parseInt(s) : 0
  return Math.max(0, Math.min(totalPages.value - 1, n || 0))
}

function prevPage() {
  if (currentPage.value > 0) { currentPage.value--; saveProgress() }
}
function nextPage() {
  if (currentPage.value < totalPages.value - 1) { currentPage.value++; saveProgress() }
}

function prevChapter() {
  const start = pageStart(currentPage.value)
  let target = -1
  for (const c of toc.value) {
    if (c.offset < start) target = c.offset
  }
  if (target >= 0) { currentPage.value = findPageByOffset(target); saveProgress() }
}

function nextChapter() {
  const start = pageStart(currentPage.value)
  const idx = toc.value.findIndex(c => c.offset > start)
  if (idx !== -1) { currentPage.value = findPageByOffset(toc.value[idx].offset); saveProgress() }
}

function goToc(item) {
  showToc.value = false
  currentPage.value = findPageByOffset(item.offset)
  saveProgress()
}

function onKey(e) {
  if (e.key === 'ArrowLeft') prevPage()
  if (e.key === 'ArrowRight') nextPage()
}

onMounted(async () => {
  try {
    const data = await api.get(`/books/${route.params.id}`)
    book.value = data.book
    if (book.value.is_online && book.value.online_url) {
      const resp = await fetch(book.value.online_url)
      if (!resp.ok) throw new Error('图书文件加载失败')
      const text = await resp.text()
      content.value = text
      toc.value = extractChapters(text)
      pages.value = paginate(text)
      currentPage.value = loadProgress()
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
  window.addEventListener('keydown', onKey)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
})
</script>

<template>
  <div v-loading="loading" class="reader">
    <div class="reader-toolbar">
      <el-button size="small" @click="router.back()">返回</el-button>
      <div v-if="book" class="reader-meta">
        <span class="book-title">{{ book.title }}</span>
        <span class="book-author">{{ book.author }}</span>
        <span v-if="toc.length" class="chapter-name" :title="chapterTitle">{{ chapterTitle }}</span>
      </div>
      <div class="reader-actions">
        <el-button size="small" v-if="toc.length" @click="showToc = true">目录</el-button>
        <el-button size="small" circle @click="fontSize = Math.max(14, fontSize - 1)">A-</el-button>
        <el-button size="small" circle @click="fontSize = Math.min(24, fontSize + 1)">A+</el-button>
      </div>
    </div>

    <div class="progress-bar"><div class="progress-fill" :style="{ width: progressPct + '%' }"></div></div>

    <div ref="bodyRef" class="reader-body">
      <div v-if="pages.length" class="page-text" :style="{ fontSize: fontSize + 'px' }">
        {{ pages[currentPage] }}
      </div>
      <div v-else-if="!loading" class="page-text end-hint">该书暂无在线内容</div>
      <div v-if="currentPage === totalPages - 1 && pages.length" class="page-text end-hint">
        — 完 —
      </div>
    </div>

    <div class="reader-footer">
      <el-button size="small" :disabled="!toc.length" @click="prevChapter">上一章</el-button>
      <el-button size="small" circle @click="prevPage" :disabled="currentPage <= 0">&lt;</el-button>
      <span class="page-num">{{ currentPage + 1 }} / {{ totalPages }}</span>
      <el-button size="small" circle @click="nextPage" :disabled="currentPage >= totalPages - 1">&gt;</el-button>
      <el-button size="small" :disabled="!toc.length" @click="nextChapter">下一章</el-button>
    </div>

    <el-drawer v-model="showToc" title="目录" size="280px">
      <div class="toc-list">
        <div
          v-for="(item, i) in toc"
          :key="i"
          class="toc-item"
          :class="{ active: chapterTitle === item.title }"
          @click="goToc(item)"
        >{{ item.title }}</div>
      </div>
    </el-drawer>
  </div>
</template>

<style scoped>
.reader {
  height: calc(100vh - 100px); /* 100vh - 顶部导航60px - el-main上下内边距40px */
  overflow: hidden;
  background: #f7f3e8;
  display: flex;
  flex-direction: column;
}
.reader-toolbar {
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 20px;
  background: #fff;
  border-bottom: 1px solid #e4e0d6;
}
.reader-meta {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  overflow: hidden;
}
.book-title { font-weight: 600; color: #303133; white-space: nowrap; }
.book-author { color: #909399; font-size: 13px; white-space: nowrap; }
.chapter-name {
  color: #606266;
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}
.reader-actions { display: flex; gap: 6px; }
.progress-bar { height: 2px; background: #e4e0d6; }
.progress-fill { height: 100%; background: #409eff; transition: width 0.2s; }

.reader-body {
  flex: 1;
  min-height: 0;
  padding: 28px 20px 20px;
  overflow-y: auto;
}
.page-text {
  max-width: 760px;
  margin: 0 auto;
  line-height: 1.9;
  color: #2c2c2c;
  font-family: Georgia, 'Noto Serif SC', 'SimSun', 'STSong', serif;
  white-space: pre-wrap;
  word-break: break-word;
}
.end-hint { text-align: center; color: #909399; margin-top: 40px; font-size: 14px; }

.reader-footer {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 10px 20px;
  background: #fff;
  border-top: 1px solid #e4e0d6;
}
.page-num { font-size: 13px; color: #606266; min-width: 60px; text-align: center; }

.toc-list { padding: 0 8px; }
.toc-item {
  padding: 10px 8px;
  font-size: 14px;
  color: #303133;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.toc-item:hover { color: #409eff; background: #f5f7fa; }
.toc-item.active { color: #409eff; font-weight: 600; }
</style>
