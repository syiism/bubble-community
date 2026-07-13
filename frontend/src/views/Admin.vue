<template>
  <div class="pb-32" style="padding-top: calc(5rem + env(safe-area-inset-top, 0px))">
    <div class="max-w-6xl mx-auto px-6">

      <!-- 标题 -->
      <div class="mb-8 scroll-animate">
        <h1 class="text-2xl sm:text-3xl font-serif font-medium text-ink tracking-tight mb-2">管理后台</h1>
        <p class="text-sm text-muted">用户 / 气泡数据总览与管理</p>
      </div>

      <div v-if="loading && !stats" class="text-center py-20 text-sm text-muted">加载中…</div>

      <template v-else>
        <!-- 统计卡片 -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-8 scroll-animate scroll-animate-delay-1">
          <div v-for="card in statCards" :key="card.label"
               class="bg-surface border border-border rounded-xl p-4 text-center">
            <div class="text-2xl font-medium text-ink">{{ card.value }}</div>
            <div class="text-xs text-muted mt-1">{{ card.label }}</div>
          </div>
        </div>

        <!-- 标签切换 -->
        <div class="flex gap-1 mb-6 border-b border-border">
          <button v-for="tab in tabs" :key="tab.key"
                  :class="[
                    'px-5 py-2.5 text-sm font-medium transition-colors rounded-t-lg -mb-px',
                    activeTab === tab.key
                      ? 'text-accent border-b-2 border-accent bg-accent/5'
                      : 'text-muted hover:text-ink hover:bg-canvas'
                  ]"
                  @click="activeTab = tab.key">
            {{ tab.label }}
          </button>
        </div>

        <!-- 用户管理 (仅 admin) -->
        <div v-if="activeTab === 'users' && isAdmin"
             class="bg-surface border border-border rounded-xl p-5">
          <div class="flex flex-wrap items-center gap-2 sm:gap-3 mb-4">
            <button v-if="selectedUsers.size"
                    class="px-3 py-1.5 text-xs sm:text-sm font-medium text-white bg-red-500/80 rounded-lg hover:bg-red-500 transition-colors"
                    @click="batchDeleteUsers">
              批量删除 ({{ selectedUsers.size }})
            </button>
            <select v-model="userRoleFilter"
                    class="w-full sm:w-auto px-3 py-1.5 bg-canvas border border-border rounded-lg text-xs sm:text-sm text-ink
                           focus:outline-none focus:border-accent transition-colors">
              <option value="">全部角色</option>
              <option value="user">普通用户</option>
              <option value="admin">管理员</option>
              <option value="reviewer">审核员</option>
            </select>
            <input v-model="userQuery" type="text" placeholder="搜索..."
                   class="w-full sm:w-auto sm:flex-1 min-w-0 sm:min-w-[160px] max-w-xs px-3 py-1.5 bg-canvas border border-border rounded-lg text-xs sm:text-sm text-ink placeholder:text-muted
                          focus:outline-none focus:border-accent transition-colors"
                   @keyup.enter="searchUsers" />
            <button class="w-full sm:w-auto px-3 py-1.5 text-xs sm:text-sm font-medium text-white bg-ink rounded-lg hover:bg-charcoal transition-colors"
                    @click="searchUsers">搜索</button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="hidden sm:table-header-group">
                <tr class="text-left text-muted text-xs border-b border-border">
                  <th class="pb-3 pr-3 w-8">
                    <input type="checkbox" :checked="allUsersSelected"
                           @change="toggleAllUsers" class="rounded border-border text-accent focus:ring-accent" />
                  </th>
                  <th class="pb-3 pr-4 font-medium">ID</th>
                  <th class="pb-3 pr-4 font-medium hidden sm:table-cell">头像</th>
                  <th class="pb-3 pr-4 font-medium">用户名</th>
                  <th class="pb-3 pr-4 font-medium hidden md:table-cell">署名</th>
                  <th class="pb-3 pr-4 font-medium">角色</th>
                  <th class="pb-3 pr-4 font-medium hidden lg:table-cell">注册时间</th>
                  <th class="pb-3 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in users" :key="u.id"
                    class="block sm:table-row mb-3 sm:mb-0 bg-surface sm:bg-transparent border sm:border-0 border-border/50 rounded-xl sm:rounded-none p-3 sm:p-0 hover:bg-canvas/50 transition-colors">
                  <td class="block sm:table-cell py-1 sm:py-3 pr-3">
                    <span class="sm:hidden text-xs text-muted mr-2">#</span>
                    <input type="checkbox" :checked="selectedUsers.has(u.id)"
                           @change="toggleUser(u.id)" class="rounded border-border text-accent focus:ring-accent" />
                  </td>
                  <td class="block sm:table-cell py-1 sm:py-3 pr-4 text-muted">
                    <span class="sm:hidden text-xs text-muted mr-2">ID</span>
                    {{ u.id }}
                  </td>
                  <td class="hidden sm:table-cell py-1 sm:py-3 pr-4">
                    <img v-if="u.avatarUrl" :src="u.avatarUrl"
                         class="w-7 h-7 rounded-full object-cover cursor-pointer hover:ring-2 hover:ring-accent/40 transition-all"
                         @click="previewAvatar(u.avatarUrl, u.username)" />
                    <div v-else
                         class="w-7 h-7 rounded-full bg-accent/10 flex items-center justify-center text-xs text-accent cursor-default">
                      {{ u.username.charAt(0).toUpperCase() }}
                    </div>
                  </td>
                  <td class="block sm:table-cell py-1 sm:py-3 pr-4 font-medium text-ink">
                    <span class="sm:hidden text-xs text-muted mr-2">用户</span>
                    <span class="inline-flex items-center gap-2">
                      <img v-if="u.avatarUrl" :src="u.avatarUrl"
                           class="sm:hidden w-6 h-6 rounded-full object-cover shrink-0 cursor-pointer hover:ring-2 hover:ring-accent/40 transition-all"
                           @click="previewAvatar(u.avatarUrl, u.username)" />
                      <div v-else class="sm:hidden w-6 h-6 rounded-full bg-accent/10 flex items-center justify-center text-xs text-accent shrink-0 cursor-default">
                        {{ u.username.charAt(0).toUpperCase() }}
                      </div>
                      <span class="truncate">{{ u.username }}</span>
                    </span>
                  </td>
                  <td class="hidden md:block md:table-cell py-1 sm:py-3 pr-4 text-muted">
                    <span class="sm:hidden text-xs text-muted mr-2">署名</span>
                    {{ u.authorName || '—' }}
                  </td>
                  <td class="block sm:table-cell py-1 sm:py-3 pr-4">
                    <span class="sm:hidden text-xs text-muted mr-2">角色</span>
                    <span :class="[
                      'inline-block px-2 py-0.5 rounded-full text-xs font-medium',
                      u.role === 'admin' ? 'bg-accent/10 text-accent' : u.role === 'reviewer' ? 'bg-amber-100 text-amber-700' : 'bg-canvas text-muted'
                    ]">{{ roleLabel(u.role) }}</span>
                  </td>
                  <td class="hidden lg:block lg:table-cell py-1 sm:py-3 pr-4 text-muted text-xs">
                    <span class="sm:hidden text-xs text-muted mr-2">注册时间</span>
                    {{ fmtDate(u.createdAt) }}
                  </td>
                  <td class="block sm:table-cell py-1 sm:py-3">
                    <span class="sm:hidden text-xs text-muted mr-2">操作</span>
                    <div class="flex items-center gap-1 sm:gap-2 mt-1 sm:mt-0">
                      <template v-if="u.role === 'user'">
                        <button class="text-xs whitespace-nowrap font-medium text-accent hover:text-accent/80 transition-colors px-2 py-1 rounded-lg bg-accent/5 sm:bg-transparent"
                                @click="setRole(u.id, u.username, 'admin')">
                          管理员
                        </button>
                        <button class="text-xs whitespace-nowrap font-medium text-amber-600 hover:text-amber-500 transition-colors px-2 py-1 rounded-lg bg-amber-50 sm:bg-transparent"
                                @click="setRole(u.id, u.username, 'reviewer')">
                          审核员
                        </button>
                      </template>
                      <button v-else-if="u.role === 'reviewer'"
                              class="text-xs whitespace-nowrap font-medium text-amber-600 hover:text-amber-500 transition-colors px-2 py-1 rounded-lg bg-amber-50 sm:bg-transparent"
                              @click="setRole(u.id, u.username, 'user')">
                        降为用户
                      </button>
                      <span v-else class="text-xs text-muted">—</span>
                      <button class="text-xs whitespace-nowrap font-medium text-ink hover:text-accent transition-colors px-2 py-1 rounded-lg bg-canvas sm:bg-transparent"
                              @click="resetPassword(u.id, u.username)">
                        密码
                      </button>
                      <button v-if="u.role === 'user'"
                              class="text-xs whitespace-nowrap font-medium text-red-500/70 hover:text-red-500 transition-colors px-2 py-1 rounded-lg bg-red-50 sm:bg-transparent"
                              @click="deleteUser(u)">
                        删除
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!users.length">
                  <td :colspan="isAdmin ? 8 : 7" class="py-8 text-center text-sm text-muted">暂无用户</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="usersTotalPages > 1" class="flex items-center justify-between mt-4 pt-4 border-t border-border">
            <div class="text-xs text-muted">共 {{ usersTotal }} 人，第 {{ usersPage }}/{{ usersTotalPages }} 页</div>
            <div class="flex gap-2">
              <button :disabled="usersPage <= 1"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40 hover:bg-canvas transition-colors"
                      @click="goUsersPage(usersPage - 1)">上一页</button>
              <button :disabled="usersPage >= usersTotalPages"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40 hover:bg-canvas transition-colors"
                      @click="goUsersPage(usersPage + 1)">下一页</button>
            </div>
          </div>
        </div>

        <!-- 气泡管理 -->
        <div v-if="activeTab === 'bubbles'"
             class="bg-surface border border-border rounded-xl p-5">
            <div class="flex flex-wrap items-center gap-2 sm:gap-3 mb-4">
              <button v-if="isAdmin && selectedBubbles.size"
                      class="px-3 py-1.5 text-xs sm:text-sm font-medium text-white bg-red-500/80 rounded-lg hover:bg-red-500 transition-colors"
                      @click="batchDeleteBubbles">
                批量删除 ({{ selectedBubbles.size }})
              </button>
              <select v-model="bubbleOfficialFilter"
                      class="px-3 py-1.5 bg-canvas border border-border rounded-lg text-xs sm:text-sm text-ink
                             focus:outline-none focus:border-accent transition-colors">
                <option value="">全部类型</option>
                <option value="1">官方</option>
                <option value="0">用户</option>
              </select>
              <select v-model="bubblePublicFilter"
                      class="px-3 py-1.5 bg-canvas border border-border rounded-lg text-xs sm:text-sm text-ink
                             focus:outline-none focus:border-accent transition-colors">
                <option value="">全部状态</option>
                <option value="1">公开</option>
                <option value="0">私有</option>
              </select>
              <select v-model="bubbleCategoryFilter"
                      class="px-3 py-1.5 bg-canvas border border-border rounded-lg text-xs sm:text-sm text-ink
                             focus:outline-none focus:border-accent transition-colors">
                <option value="">全部分区</option>
                <option value="original">原创</option>
                <option value="anime">动漫</option>
                <option value="classical">古风</option>
                <option value="other">其他</option>
              </select>
              <div class="relative w-full sm:w-auto">
                <input v-model="bubbleStartDate" type="date"
                       class="w-full px-3 py-1.5 bg-canvas border border-border rounded-lg text-xs sm:text-sm text-ink
                              focus:outline-none focus:border-accent transition-colors min-w-0"
                       @change="filterChanged" />
                <span v-if="!bubbleStartDate"
                      class="sm:hidden absolute left-3 top-1/2 -translate-y-1/2 text-xs text-muted pointer-events-none">
                  选择日期
                </span>
              </div>
              <input v-model="bubbleQuery" type="text" placeholder="搜索..."
                     class="w-full sm:w-auto sm:flex-1 min-w-0 sm:min-w-[160px] max-w-xs px-3 py-1.5 bg-canvas border border-border rounded-lg text-xs sm:text-sm text-ink placeholder:text-muted
                            focus:outline-none focus:border-accent transition-colors"
                     @keyup.enter="searchBubbles" />
              <button class="w-full sm:w-auto px-3 py-1.5 text-xs sm:text-sm font-medium text-white bg-ink rounded-lg hover:bg-charcoal transition-colors"
                      @click="searchBubbles">搜索</button>
            </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="hidden sm:table-header-group">
                <tr class="text-left text-muted text-xs border-b border-border">
                  <th v-if="isAdmin" class="pb-3 pr-3 w-8">
                    <input type="checkbox" :checked="allBubblesSelected"
                           @change="toggleAllBubbles" class="rounded border-border text-accent focus:ring-accent" />
                  </th>
                  <th class="pb-3 pr-4 font-medium">ID</th>
                  <th class="pb-3 pr-4 font-medium">名称</th>
                  <th class="pb-3 pr-4 font-medium hidden sm:table-cell">描述</th>
                  <th class="pb-3 pr-4 font-medium hidden sm:table-cell">作者</th>
                  <th class="pb-3 pr-4 font-medium hidden md:table-cell">创建者</th>
                  <th class="pb-3 pr-4 font-medium">类型</th>
                  <th class="pb-3 pr-4 font-medium">状态</th>
                  <th class="pb-3 pr-4 font-medium hidden lg:table-cell">创建时间</th>
                  <th class="pb-3 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="b in bubbles" :key="b.id"
                    class="block sm:table-row mb-3 sm:mb-0 bg-surface sm:bg-transparent border sm:border-0 border-border/50 rounded-xl sm:rounded-none p-3 sm:p-0 hover:bg-canvas/50 transition-colors">
                  <td v-if="isAdmin" class="block sm:table-cell py-1 sm:py-3 pr-3">
                    <span class="sm:hidden text-xs text-muted mr-2">#</span>
                    <input type="checkbox" :checked="selectedBubbles.has(b.id)"
                           @change="toggleBubble(b.id)" class="rounded border-border text-accent focus:ring-accent" />
                  </td>
                  <td class="block sm:table-cell py-1 sm:py-3 pr-4 text-muted">
                    <span class="sm:hidden text-xs text-muted mr-2">ID</span>
                    {{ b.id }}
                  </td>
                  <td class="block sm:table-cell py-1 sm:py-3 pr-4 font-medium text-ink truncate max-w-full sm:max-w-32" :title="b.name">
                    <span class="sm:hidden text-xs text-muted mr-2">名称</span>
                    {{ b.name }}
                    <div class="sm:hidden text-xs text-muted mt-0.5 truncate"><span class="text-xs text-muted mr-2">作者</span>{{ b.authorName || b.username || '—' }}</div>
                  </td>
                  <td class="hidden sm:table-cell py-1 sm:py-3 pr-4 text-muted max-w-32 truncate text-xs" :title="b.desc">{{ b.desc || '—' }}</td>
                  <td class="hidden sm:table-cell py-1 sm:py-3 pr-4 text-muted">{{ b.authorName || '—' }}</td>
                  <td class="hidden md:table-cell py-1 sm:py-3 pr-4 text-muted">{{ b.username || '—' }}</td>
                  <td class="block sm:table-cell py-1 sm:py-3 pr-4">
                    <span class="sm:hidden text-xs text-muted mr-2">类型</span>
                    <div class="flex items-center gap-1.5 flex-wrap">
                      <span v-if="b.official"
                            class="inline-block px-2 py-0.5 rounded-full text-xs font-medium bg-accent/10 text-accent">官方</span>
                      <span v-else class="text-xs text-muted">用户</span>
                      <span v-if="b.category && b.category !== 'original'"
                            class="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
                            :class="adminCategoryClass(b.category)">{{ adminCategoryLabel(b.category) }}</span>
                    </div>
                  </td>
                  <td class="block sm:table-cell py-1 sm:py-3 pr-4">
                    <span class="sm:hidden text-xs text-muted mr-2">状态</span>
                    <button class="text-xs font-medium transition-colors px-2 py-1 rounded-lg sm:px-0 sm:py-0 sm:rounded-none"
                            :class="b.public
                              ? 'text-green-600/70 hover:text-green-600 bg-green-50 sm:bg-transparent'
                              : 'text-muted hover:text-ink bg-canvas sm:bg-transparent'"
                            @click="toggleVisibility(b)">
                      {{ b.public ? '公开' : '私有' }}
                    </button>
                  </td>
                  <td class="hidden lg:table-cell py-1 sm:py-3 pr-4 text-muted text-xs">{{ fmtDate(b.createdAt) }}</td>
                  <td class="block sm:table-cell py-1 sm:py-3">
                    <span class="sm:hidden text-xs text-muted mr-2">操作</span>
                    <div class="flex items-center gap-1 sm:gap-2 mt-1 sm:mt-0">
                      <button v-if="isAdmin"
                              class="text-xs whitespace-nowrap font-medium text-ink hover:text-accent transition-colors px-2 py-1 rounded-lg bg-canvas sm:bg-transparent"
                              @click="openEditModal(b)">编辑</button>
                      <button class="text-xs whitespace-nowrap font-medium text-accent hover:text-accent/80 transition-colors px-2 py-1 rounded-lg bg-accent/5 sm:bg-transparent"
                              @click="previewBubble(b)">预览</button>
                      <button v-if="isAdmin"
                              class="text-xs whitespace-nowrap font-medium text-red-500/70 hover:text-red-500 transition-colors px-2 py-1 rounded-lg bg-red-50 sm:bg-transparent"
                              @click="deleteBubble(b)">删除</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!bubbles.length">
                  <td :colspan="isAdmin ? 10 : 9" class="py-8 text-center text-sm text-muted">暂无气泡</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="bubblesTotalPages > 1" class="flex items-center justify-between mt-4 pt-4 border-t border-border">
            <div class="text-xs text-muted">共 {{ bubblesTotal }} 个，第 {{ bubblesPage }}/{{ bubblesTotalPages }} 页</div>
            <div class="flex gap-2">
              <button :disabled="bubblesPage <= 1"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40 hover:bg-canvas transition-colors"
                      @click="goBubblesPage(bubblesPage - 1)">上一页</button>
              <button :disabled="bubblesPage >= bubblesTotalPages"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40 hover:bg-canvas transition-colors"
                      @click="goBubblesPage(bubblesPage + 1)">下一页</button>
            </div>
          </div>
        </div>

        <!-- 公告管理 -->
        <div v-if="activeTab === 'announcements'"
             class="bg-surface border border-border rounded-xl p-5">
          <div class="flex flex-wrap items-center gap-2 sm:gap-3 mb-4">
            <button class="w-full sm:w-auto px-3 py-1.5 text-xs sm:text-sm font-medium text-white bg-ink rounded-lg hover:bg-charcoal transition-colors"
                    @click="openAnnouncementEditor()">
              新建公告
            </button>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="hidden sm:table-header-group">
                <tr class="text-left text-muted text-xs border-b border-border">
                  <th class="pb-3 pr-4 font-medium w-12">ID</th>
                  <th class="pb-3 pr-4 font-medium">标题</th>
                  <th class="pb-3 pr-4 font-medium hidden sm:table-cell">优先级</th>
                  <th class="pb-3 pr-4 font-medium">状态</th>
                  <th class="pb-3 pr-4 font-medium hidden lg:table-cell">创建时间</th>
                  <th class="pb-3 font-medium">操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="a in announcements" :key="a.id"
                    class="block sm:table-row mb-3 sm:mb-0 bg-surface sm:bg-transparent border sm:border-0 border-border/50 rounded-xl sm:rounded-none p-3 sm:p-0 hover:bg-canvas/50 transition-colors">
                  <td class="block sm:table-cell py-1 sm:py-3 pr-4 text-muted">
                    <span class="sm:hidden text-xs text-muted mr-2">ID</span>
                    {{ a.id }}
                  </td>
                  <td class="block sm:table-cell py-1 sm:py-3 pr-4 font-medium text-ink truncate max-w-full sm:max-w-48" :title="a.title">
                    <span class="sm:hidden text-xs text-muted mr-2">标题</span>
                    {{ a.title }}
                  </td>
                  <td class="hidden sm:table-cell py-1 sm:py-3 pr-4">
                    <span class="inline-block px-2 py-0.5 rounded-full text-xs font-medium"
                          :class="a.priority === 'high' ? 'bg-red-50 text-red-600/70' : 'bg-blue-50 text-blue-600/70'">
                      {{ a.priority === 'high' ? '重要' : '普通' }}
                    </span>
                  </td>
                  <td class="block sm:table-cell py-1 sm:py-3 pr-4">
                    <span class="sm:hidden text-xs text-muted mr-2">状态</span>
                    <button class="text-xs font-medium transition-colors px-2 py-1 rounded-lg"
                            :class="a.isActive ? 'text-green-600/70 bg-green-50' : 'text-muted bg-canvas'"
                            @click="toggleAnnouncement(a)">
                      {{ a.isActive ? '启用' : '关闭' }}
                    </button>
                  </td>
                  <td class="hidden lg:table-cell py-1 sm:py-3 pr-4 text-muted text-xs">{{ fmtDate(a.createdAt) }}</td>
                  <td class="block sm:table-cell py-1 sm:py-3">
                    <span class="sm:hidden text-xs text-muted mr-2">操作</span>
                    <div class="flex items-center gap-1 sm:gap-2 mt-1 sm:mt-0">
                      <button class="text-xs whitespace-nowrap font-medium text-ink hover:text-accent transition-colors px-2 py-1 rounded-lg bg-canvas sm:bg-transparent"
                              @click="openAnnouncementEditor(a)">编辑</button>
                      <button class="text-xs whitespace-nowrap font-medium text-red-500/70 hover:text-red-500 transition-colors px-2 py-1 rounded-lg bg-red-50 sm:bg-transparent"
                              @click="deleteAnnouncement(a)">删除</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="!announcements.length">
                  <td colspan="6" class="py-8 text-center text-sm text-muted">暂无公告</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="announcementsTotalPages > 1" class="flex items-center justify-between mt-4 pt-4 border-t border-border">
            <div class="text-xs text-muted">共 {{ announcementsTotal }} 个，第 {{ announcementsPage }}/{{ announcementsTotalPages }} 页</div>
            <div class="flex gap-2">
              <button :disabled="announcementsPage <= 1"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40 hover:bg-canvas transition-colors"
                      @click="goAnnouncementsPage(announcementsPage - 1)">上一页</button>
              <button :disabled="announcementsPage >= announcementsTotalPages"
                      class="px-3 py-1 text-xs font-medium rounded-lg border border-border disabled:opacity-40 hover:bg-canvas transition-colors"
                      @click="goAnnouncementsPage(announcementsPage + 1)">下一页</button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- 编辑气泡 — 复用 Editor 组件 -->
    <Editor v-model="showBubbleEditor"
            :style="editingBubble"
            :admin="true"
            :user-list="allUsers"
            @close="showBubbleEditor = false; editingBubble = null"
            @submit="handleEditSubmit"
            @toast="toast.show"
    />

    <!-- 预览气泡 -->
    <div v-if="previewBubbleData"
         class="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-8"
         @click.self="previewBubbleData = null">
      <div class="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>
      <div class="relative bg-surface border border-border rounded-2xl p-6 sm:p-8 max-w-lg w-full shadow-xl">
        <button class="absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full bg-canvas border border-border text-muted hover:text-ink transition-colors"
                @click="previewBubbleData = null">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
        <h3 class="text-base font-medium text-ink mb-1 pr-8">{{ previewBubbleData.name }}</h3>
        <p class="text-xs text-muted mb-5">{{ previewBubbleData.desc || '无描述' }}</p>
        <div class="bg-canvas rounded-xl p-6 sm:p-10 flex items-center justify-center min-h-[200px] border border-border/50"
             v-html="previewSvg"></div>
      </div>
    </div>

    <!-- 预览头像 -->
    <div v-if="previewAvatarUrl"
         class="fixed inset-0 z-[100] flex items-center justify-center p-4"
         @click.self="previewAvatarUrl = null">
      <div class="absolute inset-0 bg-black/40 backdrop-blur-sm"></div>
      <div class="relative bg-surface border border-border rounded-2xl p-6 shadow-xl">
        <button class="absolute -top-2 -right-2 w-8 h-8 flex items-center justify-center rounded-full bg-surface border border-border text-muted hover:text-ink shadow-sm transition-colors"
                @click="previewAvatarUrl = null">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
        <img :src="previewAvatarUrl" :alt="previewAvatarName"
             class="w-48 h-48 sm:w-64 sm:h-64 rounded-full object-cover" />
        <p class="text-center text-sm text-ink mt-4 font-medium">{{ previewAvatarName }}</p>
      </div>
    </div>

    <!-- 公告编辑弹窗 -->
    <el-dialog v-model="showAnnouncementEditor" :title="editingAnnouncement ? '编辑公告' : '新建公告'"
               width="540px" top="10vh" class="editor-dialog"
               @closed="showAnnouncementEditor = false; editingAnnouncement = null">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-ink mb-2">标题</label>
          <input v-model="annForm.title" type="text" placeholder="公告标题"
                 class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors" />
        </div>
        <div>
          <label class="block text-sm font-medium text-ink mb-2">内容</label>
          <textarea v-model="annForm.content" rows="4" placeholder="公告内容"
                    class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink placeholder:text-muted focus:outline-none focus:border-accent transition-colors resize-none"></textarea>
        </div>
        <div>
          <label class="block text-sm font-medium text-ink mb-2">优先级</label>
          <select v-model="annForm.priority"
                  class="w-full px-4 py-3 bg-canvas border border-border rounded-xl text-sm text-ink focus:outline-none focus:border-accent transition-colors">
            <option value="normal">普通</option>
            <option value="high">重要</option>
          </select>
        </div>
        <div class="flex items-center gap-3">
          <input type="checkbox" v-model="annForm.isActive" class="w-4 h-4 rounded border-border text-accent focus:ring-accent" />
          <span class="text-sm text-ink">立即启用</span>
        </div>
        <button :disabled="!annForm.title.trim() || !annForm.content.trim()"
                class="w-full py-3 rounded-xl text-sm font-medium transition-colors"
                :class="annForm.title.trim() && annForm.content.trim() ? 'bg-ink text-white hover:bg-charcoal' : 'bg-border text-muted cursor-not-allowed'"
                @click="saveAnnouncement">
          {{ annSaving ? '保存中...' : (editingAnnouncement ? '保存修改' : '创建') }}
        </button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessageBox } from 'element-plus'
import { api } from '@/api'
import Editor from '@/components/Editor.vue'
import { useToast } from '@/composables/useToast'
import { getUser } from '@/stores/auth'
import { svgToImg } from '@/utils/svgHelper'

const toast = useToast()
const curUser = getUser()
const isAdmin = computed(() => curUser?.role === 'admin')
const isReviewer = computed(() => curUser?.role === 'reviewer')

const tabs = computed(() => {
  const list = []
  if (isAdmin.value) list.push({ key: 'users', label: '用户管理' })
  list.push({ key: 'bubbles', label: '气泡管理' })
  if (isAdmin.value) list.push({ key: 'announcements', label: '公告管理' })
  return list
})

const activeTab = ref('bubbles')

// ===== 统计 =====
const stats = ref(null)
const statCards = computed(() => {
  const s = stats.value
  if (!s) return []
  return [
    { label: '用户总数', value: s.totalUsers },
    { label: '气泡总数', value: s.totalBubbles },
    { label: '在线用户', value: s.onlineUsers },
    { label: '管理员', value: s.adminCount },
    { label: '总收藏数', value: s.totalFavorites },
    { label: '使用中气泡', value: s.activeBubbles },
  ]
})

// ===== 用户管理 =====
const users = ref([])
const allUsers = ref([])
const usersTotal = ref(0)
const usersPage = ref(1)
const usersPageSize = 20
const userQuery = ref('')
const userRoleFilter = ref('')
const usersTotalPages = computed(() => Math.max(1, Math.ceil(usersTotal.value / usersPageSize)))

const loadUsers = async () => {
  try {
    const data = await api.adminUsers(usersPage.value, usersPageSize, userQuery.value, userRoleFilter.value)
    users.value = data.users || []
    usersTotal.value = data.total || 0
  } catch (e) { console.error(e) }
}

const loadAllUsers = async () => {
  try {
    const data = await api.adminUsers(1, 100, '', '')
    allUsers.value = data.users || []
  } catch (e) { console.error(e) }
}

const searchUsers = () => { usersPage.value = 1; selectedUsers.value = new Set(); loadUsers() }
const goUsersPage = (p) => { usersPage.value = p; selectedUsers.value = new Set(); loadUsers() }

// ===== 选中状态（用户 & 气泡） =====
const selectedUsers = ref(new Set())
const selectedBubbles = ref(new Set())

const allUsersSelected = computed(() =>
  users.value.length > 0 && users.value.every(u => selectedUsers.value.has(u.id))
)
const allBubblesSelected = computed(() =>
  bubbles.value.length > 0 && bubbles.value.every(b => selectedBubbles.value.has(b.id))
)

const toggleUser = (id) => {
  const s = new Set(selectedUsers.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  selectedUsers.value = s
}
const toggleAllUsers = () => {
  selectedUsers.value = allUsersSelected.value ? new Set() : new Set(users.value.map(u => u.id))
}
const toggleBubble = (id) => {
  const s = new Set(selectedBubbles.value)
  if (s.has(id)) s.delete(id); else s.add(id)
  selectedBubbles.value = s
}
const toggleAllBubbles = () => {
  selectedBubbles.value = allBubblesSelected.value ? new Set() : new Set(bubbles.value.map(b => b.id))
}

const batchDeleteUsers = async () => {
  const n = selectedUsers.value.size
  if (!n) return
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${n} 个用户？<br>（管理员和当前账号会自动跳过）`,
      '批量删除用户',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning', dangerouslyUseHTMLString: true }
    )
  } catch { return }
  try {
    await api.adminBatchDeleteUsers([...selectedUsers.value])
    selectedUsers.value = new Set()
    await loadUsers()
  } catch (e) { toast.show(e.message || '操作失败') }
}

const batchDeleteBubbles = async () => {
  const n = selectedBubbles.value.size
  if (!n) return
  try {
    await ElMessageBox.confirm(
      `确定删除选中的 ${n} 个气泡？`,
      '批量删除气泡',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch { return }
  try {
    await api.adminBatchDeleteBubbles([...selectedBubbles.value])
    selectedBubbles.value = new Set()
    await loadBubbles()
  } catch (e) { toast.show(e.message || '操作失败') }
}

// ===== 气泡管理 =====
const bubbles = ref([])
const bubblesTotal = ref(0)
const bubblesPage = ref(1)
const bubblesPageSize = 20
const bubbleQuery = ref('')
const bubbleOfficialFilter = ref('')
const bubblePublicFilter = ref('')
const bubbleCategoryFilter = ref('')
const bubbleStartDate = ref('')
const bubblesTotalPages = computed(() => Math.max(1, Math.ceil(bubblesTotal.value / bubblesPageSize)))

const loadBubbles = async () => {
  try {
    const data = await api.adminBubbles(bubblesPage.value, bubblesPageSize, bubbleQuery.value,
                                        bubbleOfficialFilter.value, bubblePublicFilter.value,
                                        bubbleStartDate.value, bubbleCategoryFilter.value)
    bubbles.value = data.bubbles || []
    bubblesTotal.value = data.total || 0
  } catch (e) { console.error(e) }
}

const searchBubbles = () => { bubblesPage.value = 1; selectedBubbles.value = new Set(); loadBubbles() }
const filterChanged = () => { bubblesPage.value = 1; loadBubbles() }
const goBubblesPage = (p) => { bubblesPage.value = p; selectedBubbles.value = new Set(); loadBubbles() }

// 筛选变化时自动重新搜索
watch([userRoleFilter], () => { usersPage.value = 1; loadUsers() })
watch([bubbleOfficialFilter, bubblePublicFilter, bubbleCategoryFilter, bubbleStartDate], () => { bubblesPage.value = 1; loadBubbles() })

// ===== 公告管理 =====
const announcements = ref([])
const announcementsTotal = ref(0)
const announcementsPage = ref(1)
const announcementsPageSize = 20
const announcementsTotalPages = computed(() => Math.max(1, Math.ceil(announcementsTotal.value / announcementsPageSize)))
const showAnnouncementEditor = ref(false)
const editingAnnouncement = ref(null)
const annSaving = ref(false)
const annForm = ref({ title: '', content: '', priority: 'normal', isActive: true })

const loadAnnouncements = async () => {
  try {
    const data = await api.adminAnnouncements(announcementsPage.value, announcementsPageSize)
    announcements.value = data.announcements || []
    announcementsTotal.value = data.total || 0
  } catch (e) { console.error(e) }
}

const goAnnouncementsPage = (p) => { announcementsPage.value = p; loadAnnouncements() }

const openAnnouncementEditor = (a = null) => {
  editingAnnouncement.value = a
  if (a) {
    annForm.value = { title: a.title, content: a.content, priority: a.priority, isActive: a.isActive }
  } else {
    annForm.value = { title: '', content: '', priority: 'normal', isActive: true }
  }
  showAnnouncementEditor.value = true
}

const saveAnnouncement = async () => {
  if (!annForm.value.title.trim() || !annForm.value.content.trim()) return
  annSaving.value = true
  try {
    if (editingAnnouncement.value) {
      await api.adminUpdateAnnouncement(editingAnnouncement.value.id, annForm.value)
    } else {
      await api.adminCreateAnnouncement(annForm.value)
    }
    showAnnouncementEditor.value = false
    editingAnnouncement.value = null
    loadAnnouncements()
  } catch (e) { toast.show(e.message || '保存失败') }
  finally { annSaving.value = false }
}

const toggleAnnouncement = async (a) => {
  try {
    await api.adminUpdateAnnouncement(a.id, {
      title: a.title, content: a.content, priority: a.priority, isActive: !a.isActive,
    })
    a.isActive = !a.isActive
  } catch (e) { toast.show(e.message || '操作失败') }
}

const deleteAnnouncement = async (a) => {
  try {
    await ElMessageBox.confirm(`确定删除公告「${a.title}」？`, '删除公告', {
      confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning',
    })
  } catch { return }
  try {
    await api.adminDeleteAnnouncement(a.id)
    announcements.value = announcements.value.filter(x => x.id !== a.id)
    announcementsTotal.value = Math.max(0, announcementsTotal.value - 1)
  } catch (e) { toast.show(e.message || '删除失败') }
}

// ===== 工具 =====
const loading = ref(false)
const fmtDate = (iso) => {
  if (!iso) return ''
  return iso.slice(0, 16).replace('T', ' ')
}

const roleLabel = (role) => {
  if (role === 'admin') return '管理员'
  if (role === 'reviewer') return '审核员'
  return '用户'
}

const adminCategoryLabels = { anime: '动漫', classical: '古风', other: '其他' }
const adminCategoryLabel = (cat) => adminCategoryLabels[cat] || cat
const adminCategoryClass = (cat) => {
  if (cat === 'anime') return 'text-paleText-blue bg-pale-blue'
  if (cat === 'classical') return 'text-paleText-green bg-pale-green'
  return 'text-muted bg-canvas'
}

const roleTitle = (toRole) => {
  if (toRole === 'admin') return '管理员'
  if (toRole === 'reviewer') return '审核员'
  return '用户'
}

// ===== 用户操作 =====
const setRole = async (userId, username, role) => {
  const label = roleTitle(role)
  try {
    await ElMessageBox.confirm(`确定将 ${username} 设为${label}？`, `设为${label}`, {
      confirmButtonText: '确定', cancelButtonText: '取消', type: 'info'
    })
  } catch { return }
  try { await api.adminSetRole(userId, role); await loadUsers() }
  catch (e) { toast.show(e.message || '操作失败') }
}

const resetPassword = async (userId, username) => {
  try {
    const { value: pwd } = await ElMessageBox.prompt(
      `输入 ${username} 的新密码（至少 6 位）：`,
      '重置密码',
      { confirmButtonText: '确定', cancelButtonText: '取消', inputType: 'password', inputValidator: (v) => v && v.length >= 6 ? true : '密码长度不能少于 6 个字符' }
    )
    if (!pwd) return
    try { await api.adminSetPassword(userId, pwd); toast.show(`用户 ${username} 的密码已重置`) }
    catch (e) { toast.show(e.message || '操作失败') }
  } catch { /* 用户取消 */ }
}

const deleteUser = async (u) => {
  try {
    await ElMessageBox.confirm(
      `确定删除用户「${u.username}」(ID:${u.id})？<br>该用户的气泡、收藏等所有数据将被一并删除，不可撤销。`,
      '删除用户',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning', dangerouslyUseHTMLString: true }
    )
  } catch { return }
  try {
    await api.adminDeleteUser(u.id)
    users.value = users.value.filter(x => x.id !== u.id)
    usersTotal.value = Math.max(0, usersTotal.value - 1)
  } catch (e) { toast.show(e.message || '操作失败') }
}

// ===== 气泡操作 =====
const toggleVisibility = async (b) => {
  const newVal = !b.public
  try {
    const d = await api.adminSetBubbleVisibility(b.id, newVal)
    b.public = d.public
  } catch (e) { toast.show(e.message || '操作失败') }
}

const deleteBubble = async (b) => {
  const label = b.name || `#${b.id}`
  try {
    await ElMessageBox.confirm(
      `确定删除气泡「${label}」？<br>此操作不可撤销。`,
      '删除气泡',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning', dangerouslyUseHTMLString: true }
    )
  } catch { return }
  try { await api.adminDeleteBubble(b.id); bubbles.value = bubbles.value.filter(x => x.id !== b.id) }
  catch (e) { toast.show(e.message || '操作失败') }
}

// ===== 预览气泡 =====
const previewBubbleData = ref(null)
const previewSvg = computed(() => {
  if (!previewBubbleData.value) return ''
  return svgToImg(previewBubbleData.value.svg, 'w-full h-auto max-h-[50vh] object-contain',
                  previewBubbleData.value.color, previewBubbleData.value.textColor)
})
const previewBubble = (b) => { previewBubbleData.value = b }

// ===== 预览头像 =====
const previewAvatarUrl = ref(null)
const previewAvatarName = ref('')
const previewAvatar = (url, name) => {
  previewAvatarUrl.value = url
  previewAvatarName.value = name
}

// ===== 编辑气泡 =====
const showBubbleEditor = ref(false)
const editingBubble = ref(null)

const openEditModal = (b) => {
  editingBubble.value = b
  showBubbleEditor.value = true
}

const handleEditSubmit = async (data) => {
  try {
    await api.adminUpdateBubble(data.id, {
      name: data.name,
      desc: data.desc,
      svg: data.svg,
      color: data.color,
      textColor: data.textColor,
      public: data.public,
      category: data.category || 'original',
      authorName: data.authorName || '',
      userId: data.userId || 0,
    })
    // 更新本地行
    const idx = bubbles.value.findIndex(x => x.id === data.id)
    if (idx >= 0) {
      const newOwner = allUsers.value.find(u => u.id === data.userId)
      Object.assign(bubbles.value[idx], {
        name: data.name,
        desc: data.desc,
        public: data.public,
        category: data.category || 'original',
        authorName: data.authorName || '',
        userId: data.userId || 0,
        username: newOwner ? newOwner.username : bubbles.value[idx].username,
      })
    }
    editingBubble.value = null
    showBubbleEditor.value = false
  } catch (e) { toast.show(e.message || '保存失败') }
}

// ===== 初始化 =====
const loadAll = async () => {
  loading.value = true
  if (isAdmin.value) {
    try { const d = await api.adminStats(); stats.value = d.stats } catch (e) { console.error(e) }
  }
  loading.value = false
  const tasks = [loadBubbles()]
  if (isAdmin.value) tasks.push(loadUsers(), loadAllUsers(), loadAnnouncements())
  await Promise.all(tasks)
}

onMounted(loadAll)
</script>
