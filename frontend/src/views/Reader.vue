<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import api from '@/api'

const route = useRoute()
const router = useRouter()

const book = ref(null)
const content = ref('')
const loading = ref(true)

onMounted(async () => {
  try {
    const data = await api.get(`/books/${route.params.id}`)
    book.value = data.book
    if (book.value.is_online && book.value.online_url) {
      const resp = await fetch(book.value.online_url)
      if (!resp.ok) throw new Error('图书文件加载失败')
      content.value = await resp.text()
    }
  } catch (e) {
    ElMessage.error(e.message)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div v-loading="loading" class="reader">
    <div class="reader-head">
      <el-button @click="router.back()">返回</el-button>
      <div v-if="book" class="reader-title">
        <h2>{{ book.title }}</h2>
        <span class="reader-author">{{ book.author }}</span>
      </div>
    </div>
    <div v-if="content" class="reader-body">{{ content }}</div>
    <el-empty v-else-if="!loading" description="该书暂无在线内容" />
  </div>
</template>

<style scoped>
.reader { background: #fff; border-radius: 8px; padding: 24px; }
.reader-head {
  display: flex; align-items: center; gap: 20px;
  border-bottom: 1px solid #ebeef5; padding-bottom: 16px; margin-bottom: 16px;
}
.reader-title h2 { font-size: 20px; color: #303133; display: inline; margin-right: 12px; }
.reader-author { color: #909399; font-size: 13px; }
.reader-body {
  max-width: 860px; margin: 0 auto;
  white-space: pre-wrap; line-height: 1.9; font-size: 15px; color: #303133;
  max-height: calc(100vh - 240px); overflow: auto;
  padding: 0 12px;
}
</style>
