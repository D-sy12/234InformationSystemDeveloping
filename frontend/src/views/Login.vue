<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import SlideVerify from '@/components/SlideVerify.vue'
import api from '@/api'
import { useUserStore } from '@/store/user'

const router = useRouter()
const route = useRoute()
const store = useUserStore()

const formRef = ref()
const form = reactive({ account: '', password: '' })
const rules = {
  account: [{ required: true, message: '请输入用户名或邮箱', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

const captchaOk = ref(false)
const captchaRef = ref()
const submitting = ref(false)

async function submit() {
  if (!captchaOk.value) return ElMessage.warning('请先完成滑块验证')
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const data = await api.post('/auth/login', form)
    store.setLogin(data.token, data.user)
    ElMessage.success(`欢迎回来，${data.user.username}`)
    router.push(route.query.redirect || (data.user.role === 'admin' ? '/admin' : '/'))
  } catch (e) {
    ElMessage.error(e.message)
    captchaOk.value = false
    captchaRef.value?.reset() // 重置滑块
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 class="auth-title">登录</h2>
      <el-form ref="formRef" :model="form" :rules="rules" size="large" @keyup.enter="submit">
        <el-form-item prop="account">
          <el-input v-model="form.account" placeholder="用户名 / 邮箱" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="密码" />
        </el-form-item>
      </el-form>

      <div class="captcha-label">行为验证：</div>
      <SlideVerify ref="captchaRef" @success="captchaOk = true" />

      <el-button type="primary" size="large" class="submit" :loading="submitting" :disabled="!captchaOk" @click="submit">
        登录
      </el-button>
      <div class="tip">还没有账号？<router-link to="/register">去注册</router-link></div>
    </el-card>
  </div>
</template>

<style scoped>
.auth-page { display: flex; justify-content: center; padding: 40px 0; }
.auth-card { width: 400px; padding: 8px 12px; }
.auth-title { text-align: center; margin-bottom: 20px; color: #303133; }
.captcha-label { font-size: 13px; color: #606266; margin-bottom: 8px; }
.submit { width: 100%; margin-top: 16px; }
.tip { text-align: center; margin-top: 14px; font-size: 13px; color: #909399; }
.tip a { color: #409eff; text-decoration: none; }
</style>
