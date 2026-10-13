<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { useUserStore } from '@/store/user'

const store = useUserStore()
const rows = ref([])
const loading = ref(false)

const statusMap = {
  pending: ['待审核', 'info'],
  borrowed: ['借阅中', 'primary'],
  due_soon: ['即将到期', 'warning'],
  overdue: ['已逾期', 'danger'],
  returned: ['已归还', 'success'],
  cancelled: ['已取消', 'info'],
}

const active = computed(() => rows.value.filter((r) => ['pending', 'borrowed'].includes(r.status)))
const history = computed(() => rows.value.filter((r) => ['returned', 'cancelled'].includes(r.status)))

function fmt(s) {
  return s ? s.replace('T', ' ').slice(0, 16) : '-'
}

function dueInfo(row) {
  if (row.display_status === 'overdue') {
    const days = Math.floor((Date.now() - new Date(row.due_date)) / 86400000) + 1
    return { text: `已逾期 ${days} 天`, tag: 'danger' }
  }
  if (row.display_status === 'due_soon') {
    const hours = Math.max(1, Math.floor((new Date(row.due_date) - Date.now()) / 3600000))
    return { text: `${hours} 小时后到期`, tag: 'warning' }
  }
  if (row.status === 'borrowed') {
    const days = Math.floor((new Date(row.due_date) - Date.now()) / 86400000)
    return { text: `剩余 ${days} 天`, tag: 'success' }
  }
  return { text: '-', tag: 'info' }
}

async function load() {
  loading.value = true
  try {
    const data = await api.get('/reservations/mine')
    rows.value = data.reservations
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

async function cancel(row) {
  try {
    const data = await api.post(`/reservations/${row.id}/cancel`)
    ElMessage.success(data.message)
    load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function giveBack(row) {
  try {
    const data = await api.post(`/reservations/${row.id}/return`)
    ElMessage.success(data.message)
    load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(load)
</script>

<template>
  <div v-loading="loading" class="profile">
    <el-card class="user-card">
      <div class="user-info">
        <div class="avatar">{{ store.user?.username?.charAt(0)?.toUpperCase() }}</div>
        <div class="detail">
          <div class="name">
            {{ store.user?.username }}
            <el-tag v-if="store.user?.role === 'admin'" size="small" type="danger">管理员</el-tag>
          </div>
          <div class="email">{{ store.user?.email }}</div>
          <div class="join">注册时间：{{ fmt(store.user?.created_at) }}</div>
        </div>
      </div>
    </el-card>

    <el-tabs class="tabs" type="border-card">
      <el-tab-pane :label="`我的借阅 / 预约（${active.length}）`">
        <el-table :data="active" stripe>
          <el-table-column label="封面" width="70">
            <template #default="{ row }">
              <img v-if="row.book.cover_url" :src="row.book.cover_url" class="thumb" alt="" />
              <div v-else class="thumb thumb-fallback">{{ row.book.title?.charAt(0) }}</div>
            </template>
          </el-table-column>
          <el-table-column label="书名" prop="book.title" min-width="160" show-overflow-tooltip />
          <el-table-column label="作者" prop="book.author" width="120" show-overflow-tooltip />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="statusMap[row.display_status]?.[1]">
                {{ statusMap[row.display_status]?.[0] }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="借出 / 预约时间" width="150">
            <template #default="{ row }">{{ fmt(row.borrowed_at || row.reserved_at) }}</template>
          </el-table-column>
          <el-table-column label="应还时间" width="150">
            <template #default="{ row }">{{ fmt(row.due_date) }}</template>
          </el-table-column>
          <el-table-column label="倒计时" width="150">
            <template #default="{ row }">
              <el-tag size="small" :type="dueInfo(row).tag" effect="plain">{{ dueInfo(row).text }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button v-if="row.status === 'pending'" link type="warning" @click="cancel(row)">取消预约</el-button>
              <el-button v-if="row.status === 'borrowed'" link type="primary" @click="giveBack(row)">归还</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!active.length" description="暂无借阅和预约记录" :image-size="80" />
      </el-tab-pane>

      <el-tab-pane :label="`历史记录（${history.length}）`">
        <el-table :data="history" stripe>
          <el-table-column label="封面" width="70">
            <template #default="{ row }">
              <img v-if="row.book.cover_url" :src="row.book.cover_url" class="thumb" alt="" />
              <div v-else class="thumb thumb-fallback">{{ row.book.title?.charAt(0) }}</div>
            </template>
          </el-table-column>
          <el-table-column label="书名" prop="book.title" min-width="160" show-overflow-tooltip />
          <el-table-column label="状态" width="110">
            <template #default="{ row }">
              <el-tag size="small" :type="statusMap[row.display_status]?.[1]">
                {{ statusMap[row.display_status]?.[0] }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="预约时间" width="150">
            <template #default="{ row }">{{ fmt(row.reserved_at) }}</template>
          </el-table-column>
          <el-table-column label="借出时间" width="150">
            <template #default="{ row }">{{ fmt(row.borrowed_at) }}</template>
          </el-table-column>
          <el-table-column label="应还时间" width="150">
            <template #default="{ row }">{{ fmt(row.due_date) }}</template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!history.length" description="暂无历史记录" :image-size="80" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.profile { padding-bottom: 24px; }
.user-card { margin-bottom: 16px; }
.user-info { display: flex; align-items: center; gap: 20px; }
.avatar {
  width: 64px; height: 64px; border-radius: 50%;
  background: linear-gradient(135deg, #409eff, #7b5ce0);
  color: #fff; font-size: 28px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
.name { font-size: 18px; font-weight: 600; color: #303133; display: flex; align-items: center; gap: 8px; }
.email { color: #909399; font-size: 13px; margin-top: 4px; }
.join { color: #c0c4cc; font-size: 12px; margin-top: 2px; }
.tabs { background: #fff; }
.thumb { width: 40px; height: 54px; object-fit: cover; border-radius: 4px; display: block; }
.thumb-fallback {
  background: linear-gradient(135deg, #909399, #606266);
  color: #fff; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
}
</style>
