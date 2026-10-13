<script setup>
import { nextTick, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as echarts from 'echarts'
import api from '@/api'

const tab = ref('books')
const books = ref([])
const borrows = ref([])
const loading = ref(false)

const statusMap = {
  pending: ['待审核', 'info'],
  borrowed: ['借阅中', 'primary'],
  due_soon: ['即将到期', 'warning'],
  overdue: ['已逾期', 'danger'],
  returned: ['已归还', 'success'],
  cancelled: ['已取消', 'info'],
}
const statusName = {
  pending: '待审核',
  borrowed: '借阅中',
  returned: '已归还',
  cancelled: '已取消',
  overdue: '已逾期',
}

// ---- 图书管理 ----
const addDialog = ref(false)
const addFormRef = ref()
const addForm = reactive({
  title: '', author: '', isbn: '', category: '',
  description: '', is_online: true, online_url: '', total_copies: 1, cover_url: '',
})
const addRules = {
  title: [{ required: true, message: '请输入书名', trigger: 'blur' }],
}

function fmt(s) {
  return s ? s.replace('T', ' ').slice(0, 16) : '-'
}

async function loadBooks() {
  loading.value = true
  try {
    const data = await api.get('/books', { params: { type: 'all' } })
    books.value = data.books
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function submitAdd() {
  const valid = await addFormRef.value.validate().catch(() => false)
  if (!valid) return
  try {
    const data = await api.post('/admin/books', { ...addForm })
    ElMessage.success(data.message)
    addDialog.value = false
    Object.assign(addForm, {
      title: '', author: '', isbn: '', category: '',
      description: '', is_online: true, online_url: '', total_copies: 1, cover_url: '',
    })
    loadBooks()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function editCopies(book) {
  ElMessageBox.prompt(`修改《${book.title}》的馆藏总数`, '修改馆藏数量', {
    inputValue: String(book.total_copies),
    inputPattern: /^\d+$/,
    inputErrorMessage: '请输入非负整数',
  })
    .then(async ({ value }) => {
      const data = await api.put(`/admin/books/${book.id}/copies`, { total_copies: Number(value) })
      ElMessage.success(data.message)
      loadBooks()
    })
    .catch(() => {})
}

// ---- 借阅管理 ----
async function loadBorrows() {
  try {
    const data = await api.get('/admin/reservations')
    borrows.value = data.reservations
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function rowClass({ row }) {
  if (row.display_status === 'overdue') return 'row-overdue'
  if (row.display_status === 'due_soon') return 'row-warn'
  return ''
}

async function approve(row) {
  try {
    const data = await api.post(`/admin/reservations/${row.id}/approve`)
    ElMessage.success(data.message)
    loadBorrows()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function markReturned(row) {
  try {
    const data = await api.post(`/admin/reservations/${row.id}/returned`)
    ElMessage.success(data.message)
    loadBorrows()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function remind(row) {
  try {
    const data = await api.post(`/admin/reservations/${row.id}/remind`)
    ElMessage.success(data.message)
  } catch (e) {
    ElMessage.error(e.message)
  }
}

// ---- 数据统计 ----
const stats = ref(null)
const pieRef = ref(null)
const statusRef = ref(null)
const barRef = ref(null)

async function loadStats() {
  try {
    stats.value = await api.get('/admin/stats')
    await nextTick()
    renderCharts()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

function renderCharts() {
  const build = (el, option) => {
    if (!el) return
    echarts.getInstanceByDom(el)?.dispose()
    echarts.init(el).setOption(option)
  }
  build(pieRef.value, {
    title: { text: '图书分类分布', left: 'center' },
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: '55%',
      data: stats.value.categories.map((c) => ({ name: c.name, value: c.count })),
    }],
  })
  build(statusRef.value, {
    title: { text: '借阅状态分布', left: 'center' },
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie', radius: '55%',
      data: Object.entries(stats.value.status_dist).map(([k, v]) => ({ name: statusName[k] || k, value: v })),
    }],
  })
  const top = [...stats.value.top_borrowed].reverse()
  build(barRef.value, {
    title: { text: '热门借阅 TOP5', left: 'center' },
    tooltip: {},
    grid: { left: 180, right: 40 },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: { type: 'category', data: top.map((t) => t.title) },
    series: [{ type: 'bar', data: top.map((t) => t.count) }],
  })
}

watch(tab, (t) => {
  if (t === 'borrows' && !borrows.value.length) loadBorrows()
  if (t === 'stats' && !stats.value) loadStats()
})

onMounted(loadBooks)
</script>

<template>
  <div class="admin">
    <el-tabs v-model="tab" type="border-card">
      <!-- 图书管理 -->
      <el-tab-pane label="图书管理" name="books">
        <div class="tab-toolbar">
          <el-button type="primary" @click="addDialog = true">添加图书</el-button>
        </div>
        <el-table v-loading="loading" :data="books" stripe>
          <el-table-column label="封面" width="70">
            <template #default="{ row }">
              <img v-if="row.cover_url" :src="row.cover_url" class="thumb" alt="" />
              <div v-else class="thumb thumb-fallback">{{ row.title?.charAt(0) }}</div>
            </template>
          </el-table-column>
          <el-table-column label="书名" prop="title" min-width="180" show-overflow-tooltip />
          <el-table-column label="作者" prop="author" width="130" show-overflow-tooltip />
          <el-table-column label="分类" prop="category" width="110" />
          <el-table-column label="类型" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.is_online ? 'success' : 'warning'">
                {{ row.is_online ? '在线' : '实体' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="馆藏（可借/总数）" width="140">
            <template #default="{ row }">
              <span v-if="!row.is_online">{{ row.available_copies }} / {{ row.total_copies }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="130" fixed="right">
            <template #default="{ row }">
              <el-button v-if="!row.is_online" link type="primary" @click="editCopies(row)">修改数量</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 借阅管理 -->
      <el-tab-pane label="借阅管理" name="borrows">
        <div class="tab-toolbar">
          <el-button type="primary" plain @click="loadBorrows">刷新列表（自动发送到期提醒）</el-button>
        </div>
        <el-table :data="borrows" stripe :row-class-name="rowClass">
          <el-table-column label="用户" prop="user.username" width="120" show-overflow-tooltip />
          <el-table-column label="邮箱" prop="user.email" width="200" show-overflow-tooltip />
          <el-table-column label="图书" prop="book.title" min-width="170" show-overflow-tooltip />
          <el-table-column label="预约时间" width="145">
            <template #default="{ row }">{{ fmt(row.reserved_at) }}</template>
          </el-table-column>
          <el-table-column label="借出时间" width="145">
            <template #default="{ row }">{{ fmt(row.borrowed_at) }}</template>
          </el-table-column>
          <el-table-column label="应还时间" width="145">
            <template #default="{ row }">{{ fmt(row.due_date) }}</template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="statusMap[row.display_status]?.[1]">
                {{ statusMap[row.display_status]?.[0] }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="提醒" width="80">
            <template #default="{ row }">
              <el-tag size="small" :type="row.reminded ? 'success' : 'info'" effect="plain">
                {{ row.reminded ? '已发' : '未发' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="210">
            <template #default="{ row }">
              <el-button v-if="row.status === 'pending'" link type="primary" @click="approve(row)">通过并出借</el-button>
              <el-button v-if="row.status === 'borrowed'" link type="success" @click="markReturned(row)">标记归还</el-button>
              <el-button v-if="row.status === 'borrowed'" link type="danger" @click="remind(row)">发送提醒</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>

      <!-- 数据统计 -->
      <el-tab-pane label="数据统计" name="stats">
        <div v-if="stats" class="charts">
          <div ref="pieRef" class="chart" />
          <div ref="statusRef" class="chart" />
          <div ref="barRef" class="chart chart-wide" />
        </div>
        <el-empty v-else description="加载中..." />
      </el-tab-pane>
    </el-tabs>

    <!-- 添加图书弹窗 -->
    <el-dialog v-model="addDialog" title="添加图书" width="520px">
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="90px">
        <el-form-item label="书名" prop="title">
          <el-input v-model="addForm.title" placeholder="必填" />
        </el-form-item>
        <el-form-item label="作者">
          <el-input v-model="addForm.author" />
        </el-form-item>
        <el-form-item label="分类">
          <el-input v-model="addForm.category" placeholder="如：计算机科学" />
        </el-form-item>
        <el-form-item label="ISBN">
          <el-input v-model="addForm.isbn" />
        </el-form-item>
        <el-form-item label="类型">
          <el-switch v-model="addForm.is_online" active-text="在线图书" inactive-text="实体图书" />
        </el-form-item>
        <el-form-item v-if="addForm.is_online" label="阅读地址">
          <el-input v-model="addForm.online_url" placeholder="/static/books/xxx.txt 或外部链接" />
        </el-form-item>
        <el-form-item v-else label="馆藏数量">
          <el-input-number v-model="addForm.total_copies" :min="1" />
        </el-form-item>
        <el-form-item label="封面地址">
          <el-input v-model="addForm.cover_url" placeholder="留空则使用默认占位封面" />
        </el-form-item>
        <el-form-item label="简介">
          <el-input v-model="addForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialog = false">取消</el-button>
        <el-button type="primary" @click="submitAdd">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.admin { padding-bottom: 24px; }
.tab-toolbar { margin-bottom: 14px; display: flex; justify-content: flex-end; }
.thumb { width: 40px; height: 54px; object-fit: cover; border-radius: 4px; display: block; }
.thumb-fallback {
  background: linear-gradient(135deg, #909399, #606266);
  color: #fff; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
}
.charts { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.chart { height: 320px; border: 1px solid #ebeef5; border-radius: 6px; }
.chart-wide { grid-column: 1 / -1; }

/* 逾期标红 / 即将到期标黄 */
:deep(.row-overdue td.el-table__cell) { background: #fef0f0 !important; }
:deep(.row-warn td.el-table__cell) { background: #fdf6ec !important; }
</style>
