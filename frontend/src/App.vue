<script setup>
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/user'

const router = useRouter()
const store = useUserStore()

function logout() {
  store.logout()
  ElMessage.success('已退出登录')
  router.push('/')
}
</script>

<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="logo" @click="router.push('/')">
        <span class="logo-mark">图书管理系统</span>
      </div>
      <el-menu mode="horizontal" :default-active="$route.path" router :ellipsis="false" class="menu">
        <el-menu-item index="/">图书浏览</el-menu-item>
        <el-menu-item v-if="store.isLoggedIn" index="/profile">个人中心</el-menu-item>
        <el-menu-item v-if="store.isAdmin" index="/admin">管理后台</el-menu-item>
      </el-menu>
      <div class="user-area">
        <template v-if="store.isLoggedIn">
          <span class="welcome">{{ store.user?.username }}</span>
          <el-button link type="danger" @click="logout">退出</el-button>
        </template>
        <template v-else>
          <el-button link type="primary" @click="router.push('/login')">登录</el-button>
          <el-button link @click="router.push('/register')">注册</el-button>
        </template>
      </div>
    </el-header>
    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<style>
* { margin: 0; padding: 0; }
body { background: #f5f7fa; font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', sans-serif; }

.layout { min-height: 100vh; }
.header {
  display: flex; align-items: center; gap: 24px;
  background: #fff; border-bottom: 1px solid #e4e7ed;
  position: sticky; top: 0; z-index: 100;
}
.logo { cursor: pointer; white-space: nowrap; }
.logo-mark { font-size: 18px; font-weight: 700; color: #409eff; }
.menu { flex: 1; border-bottom: none !important; }
.user-area { white-space: nowrap; display: flex; align-items: center; gap: 4px; }
.welcome { color: #606266; margin-right: 8px; }
.main { max-width: 1400px; margin: 0 auto; width: 100%; }
</style>
