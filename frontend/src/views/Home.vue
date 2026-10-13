<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'
import { useUserStore } from '@/store/user'

const router = useRouter()
const store = useUserStore()

const books = ref([])
const categories = ref([])
const keyword = ref('')
const category = ref('')
const type = ref('all')
const loading = ref(false)

// 游客查看实体图书分类时，显示登录引导提示
const guestPhysical = computed(() => !store.isLoggedIn && type.value === 'physical')

async function load() {
  loading.value = true
  try {
    const params = {}
    if (keyword.value) params.q = keyword.value
    if (category.value) params.category = category.value
    if (type.value !== 'all') params.type = type.value
    const data = await api.get('/books', { params })
    books.value = data.books
    categories.value = data.categories
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
}

function coverStyle(id) {
  const hues = [210, 160, 280, 20, 340, 90, 260, 190]
  const h = hues[id % hues.length]
  return { background: `linear-gradient(135deg, hsl(${h},70%,55%), hsl(${h + 40},70%,40%))` }
}

async function reserve(book) {
  if (!store.isLoggedIn) {
    ElMessage.warning('预约借阅请先登录')
    return router.push('/login')
  }
  try {
    const data = await api.post('/reservations', { book_id: book.id })
    ElMessage.success(data.message)
    load()
  } catch (e) {
    ElMessage.error(e.message)
  }
}

onMounted(load)
</script>

<template>
  <div class="home">
    <div class="toolbar">
      <el-radio-group v-model="type" @change="load">
        <el-radio-button value="all">全部</el-radio-button>
        <el-radio-button value="online">在线图书</el-radio-button>
        <el-radio-button value="physical">实体图书</el-radio-button>
      </el-radio-group>
      <el-select v-model="category" clearable placeholder="全部分类" style="width: 150px" @change="load">
        <el-option v-for="c in categories" :key="c" :label="c" :value="c" />
      </el-select>
      <el-input
        v-model="keyword"
        placeholder="搜索书名 / 作者"
        clearable
        style="width: 240px"
        @keyup.enter="load"
        @clear="load"
      >
        <template #append>
          <el-button @click="load">搜索</el-button>
        </template>
      </el-input>
    </div>

    <el-empty v-if="guestPhysical" style="padding: 60px 0">
      <template #description>
        <p class="tip-title">实体图书需登录后查看与借阅</p>
        <p class="tip-sub">注册账号即可在线预约实体图书，每本借阅期 7 天，到期前会邮件提醒还书</p>
      </template>
      <el-button type="primary" @click="router.push('/login')">登录</el-button>
      <el-button @click="router.push('/register')">免费注册</el-button>
    </el-empty>

    <div v-else v-loading="loading" class="grid">
      <el-card v-for="book in books" :key="book.id" class="book-card" shadow="hover" :body-style="{ padding: 0 }">
        <div class="cover" @click="book.is_online && router.push(`/read/${book.id}`)">
          <img v-if="book.cover_url" :src="book.cover_url" alt="" @error="book.cover_url = ''" />
          <div v-else class="fallback" :style="coverStyle(book.id)">
            <span class="fallback-title">{{ book.title }}</span>
            <span class="fallback-author">{{ book.author }}</span>
          </div>
        </div>
        <div class="info">
          <div class="title" :title="book.title">{{ book.title }}</div>
          <div class="meta">
            <el-tag size="small" type="info">{{ book.category || '未分类' }}</el-tag>
            <el-tag size="small" :type="book.is_online ? 'success' : 'warning'">
              {{ book.is_online ? '在线' : '实体' }}
            </el-tag>
          </div>
          <div class="author">{{ book.author || '佚名' }}</div>
          <div class="desc" :title="book.description">{{ book.description || '暂无简介' }}</div>
          <div class="actions">
            <template v-if="book.is_online">
              <el-button type="primary" size="small" style="width: 100%" @click="router.push(`/read/${book.id}`)">
                在线阅读
              </el-button>
            </template>
            <template v-else>
              <span class="copies">可借 {{ book.available_copies }} / {{ book.total_copies }}</span>
              <el-button
                type="primary"
                size="small"
                :disabled="book.available_copies <= 0"
                @click="reserve(book)"
              >
                预约借阅
              </el-button>
            </template>
          </div>
        </div>
      </el-card>
      <el-empty v-if="!loading && !books.length" description="没有找到图书" style="grid-column: 1 / -1" />
    </div>
  </div>
</template>

<style scoped>
.toolbar { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
.tip-title { font-size: 17px; font-weight: 600; color: #303133; margin: 0 0 6px; }
.tip-sub { font-size: 13px; color: #909399; margin: 0; }

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 16px;
}
.book-card { cursor: default; }
.cover { height: 250px; overflow: hidden; background: #eee; cursor: pointer; }
.cover img { width: 100%; height: 100%; object-fit: cover; display: block; }
.fallback {
  width: 100%; height: 100%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; padding: 16px; box-sizing: border-box; text-align: center;
}
.fallback-title { color: #fff; font-size: 18px; font-weight: 600; word-break: break-all; }
.fallback-author { color: rgba(255, 255, 255, 0.85); font-size: 13px; }
.info { padding: 12px 14px 14px; }
.title {
  font-size: 15px; font-weight: 600; color: #303133;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.meta { display: flex; gap: 6px; margin: 8px 0 4px; }
.author { font-size: 12px; color: #909399; }
.desc {
  font-size: 12px; color: #909399; margin: 6px 0 10px; height: 32px;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.actions { display: flex; align-items: center; justify-content: space-between; }
.copies { font-size: 12px; color: #67c23a; }
</style>
