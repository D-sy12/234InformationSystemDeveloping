<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import SlideVerify from '@/components/SlideVerify.vue'
import api from '@/api'

const router = useRouter()

const formRef = ref()
const form = reactive({
  username: '',
  email: '',
  password: '',
  confirm: '',
  code: '',
})

const validateConfirm = (rule, value, cb) => {
  if (value !== form.password) return cb(new Error('两次输入的密码不一致'))
  cb()
}
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '长度 2-20 个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
  ],
  confirm: [{ required: true, validator: validateConfirm, trigger: 'blur' }],
  code: [{ required: true, message: '请输入邮箱验证码', trigger: 'blur' }],
}

const captchaOk = ref(false)
const captchaRef = ref()
const submitting = ref(false)
const cooldown = ref(0)
let timer = null

async function sendCode() {
  if (!/^[\w.+-]+@[\w-]+(\.[\w-]+)+$/.test(form.email)) {
    return ElMessage.warning('请先填写正确的邮箱')
  }
  try {
    const data = await api.post('/auth/send-code', { email: form.email })
    ElMessage.success(data.message)
    cooldown.value = 60
    timer = setInterval(() => {
      cooldown.value--
      if (cooldown.value <= 0) clearInterval(timer)
    }, 1000)
  } catch (e) {
    ElMessage.error(e.message)
  }
}

async function submit() {
  if (!captchaOk.value) return ElMessage.warning('请先完成滑块验证')
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    const data = await api.post('/auth/register', {
      username: form.username,
      email: form.email,
      password: form.password,
      code: form.code,
    })
    ElMessage.success(data.message)
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.message)
    captchaOk.value = false
    captchaRef.value?.reset()
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <el-card class="auth-card">
      <h2 class="auth-title">注册</h2>
      <el-form ref="formRef" :model="form" :rules="rules" size="large">
        <el-form-item prop="username">
          <el-input v-model="form.username" placeholder="用户名（2-20 个字符）" />
        </el-form-item>
        <el-form-item prop="email">
          <el-input v-model="form.email" placeholder="邮箱" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="密码（至少 6 位）" />
        </el-form-item>
        <el-form-item prop="confirm">
          <el-input v-model="form.confirm" type="password" show-password placeholder="确认密码" />
        </el-form-item>
        <el-form-item prop="code">
          <div class="code-row">
            <el-input v-model="form.code" placeholder="邮箱验证码" />
            <el-button :disabled="cooldown > 0" @click="sendCode">
              {{ cooldown > 0 ? `${cooldown}s 后重发` : '发送验证码' }}
            </el-button>
          </div>
        </el-form-item>
      </el-form>

      <div class="captcha-label">行为验证：</div>
      <SlideVerify ref="captchaRef" @success="captchaOk = true" />

      <el-button type="primary" size="large" class="submit" :loading="submitting" :disabled="!captchaOk" @click="submit">
        注册
      </el-button>
      <div class="tip">已有账号？<router-link to="/login">去登录</router-link></div>
    </el-card>
  </div>
</template>

<style scoped>
.auth-page { display: flex; justify-content: center; padding: 40px 0; }
.auth-card { width: 420px; padding: 8px 12px; }
.auth-title { text-align: center; margin-bottom: 20px; color: #303133; }
.code-row { display: flex; gap: 8px; width: 100%; }
.captcha-label { font-size: 13px; color: #606266; margin-bottom: 8px; }
.submit { width: 100%; margin-top: 16px; }
.tip { text-align: center; margin-top: 14px; font-size: 13px; color: #909399; }
.tip a { color: #409eff; text-decoration: none; }
</style>
