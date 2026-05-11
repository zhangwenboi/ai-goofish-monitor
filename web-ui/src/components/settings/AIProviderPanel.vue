<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Plus, Pencil, Trash2, RotateCcw } from 'lucide-vue-next'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { toast } from '@/components/ui/toast'
import {
  type AIProvider, type AIProviderCreate, type AIProviderUpdate,
  getAIProviders, createAIProvider, updateAIProvider, deleteAIProvider, resetAIProviderQuota,
} from '@/api/settings'

const { t } = useI18n()
const providers = ref<AIProvider[]>([])
const isLoading = ref(false)
const showForm = ref(false)
const editingId = ref<number | null>(null)

const form = reactive<AIProviderCreate>({
  name: '',
  base_url: '',
  api_key: '',
  model_name: '',
  proxy_url: '',
  quota_limit: undefined,
  priority: 0,
  enabled: true,
})

// PLACEHOLDER_CONTINUE

async function fetchProviders() {
  isLoading.value = true
  try {
    providers.value = await getAIProviders()
  } catch (e) {
    toast({ title: t('settings.aiProviders.fetchFailed'), description: (e as Error).message, variant: 'destructive' })
  } finally {
    isLoading.value = false
  }
}

function resetForm() {
  form.name = ''
  form.base_url = ''
  form.api_key = ''
  form.model_name = ''
  form.proxy_url = ''
  form.quota_limit = undefined
  form.priority = 0
  form.enabled = true
}

function handleAdd() {
  editingId.value = null
  resetForm()
  showForm.value = true
}

function handleEdit(provider: AIProvider) {
  editingId.value = provider.id
  form.name = provider.name
  form.base_url = provider.base_url
  form.api_key = ''
  form.model_name = provider.model_name
  form.proxy_url = provider.proxy_url || ''
  form.quota_limit = provider.quota_limit
  form.priority = provider.priority
  form.enabled = provider.enabled
  showForm.value = true
}

function handleCancel() {
  showForm.value = false
  editingId.value = null
  resetForm()
}

async function handleSubmit() {
  if (!form.name || !form.base_url || !form.model_name) {
    toast({ title: t('settings.aiProviders.validationError'), variant: 'destructive' })
    return
  }
  try {
    if (editingId.value) {
      const data: AIProviderUpdate = {
        name: form.name,
        base_url: form.base_url,
        model_name: form.model_name,
        proxy_url: form.proxy_url || null,
        quota_limit: form.quota_limit || null,
        priority: form.priority,
        enabled: form.enabled,
      }
      if (form.api_key) data.api_key = form.api_key
      await updateAIProvider(editingId.value, data)
      toast({ title: t('settings.aiProviders.updated') })
    } else {
      if (!form.api_key) {
        toast({ title: t('settings.aiProviders.apiKeyRequired'), variant: 'destructive' })
        return
      }
      await createAIProvider(form)
      toast({ title: t('settings.aiProviders.created') })
    }
    showForm.value = false
    editingId.value = null
    resetForm()
    await fetchProviders()
  } catch (e) {
    toast({ title: t('settings.aiProviders.saveFailed'), description: (e as Error).message, variant: 'destructive' })
  }
}

async function handleDelete(id: number) {
  try {
    await deleteAIProvider(id)
    toast({ title: t('settings.aiProviders.deleted') })
    await fetchProviders()
  } catch (e) {
    toast({ title: t('settings.aiProviders.deleteFailed'), description: (e as Error).message, variant: 'destructive' })
  }
}

async function handleResetQuota(id: number) {
  try {
    await resetAIProviderQuota(id)
    toast({ title: t('settings.aiProviders.quotaReset') })
    await fetchProviders()
  } catch (e) {
    toast({ title: t('settings.aiProviders.resetFailed'), description: (e as Error).message, variant: 'destructive' })
  }
}

onMounted(fetchProviders)
</script>

<template>
  <Card class="app-surface overflow-hidden border-none">
    <CardHeader>
      <div class="flex items-center justify-between">
        <div>
          <CardTitle>{{ t('settings.aiProviders.title') }}</CardTitle>
          <CardDescription>{{ t('settings.aiProviders.description') }}</CardDescription>
        </div>
        <Button size="sm" @click="handleAdd"><Plus class="h-4 w-4" />{{ t('settings.aiProviders.add') }}</Button>
      </div>
    </CardHeader>
    <CardContent>
      <div v-if="isLoading" class="py-8 text-center text-sm text-slate-500">{{ t('common.loading') }}</div>
      <div v-else-if="!providers.length && !showForm" class="py-8 text-center text-sm text-slate-500">
        {{ t('settings.aiProviders.empty') }}
      </div>
      <div v-else class="space-y-3">
        <div v-for="provider in providers" :key="provider.id" class="flex items-center justify-between rounded-lg border p-4">
          <div class="space-y-1">
            <div class="flex items-center gap-2">
              <span class="font-medium">{{ provider.name }}</span>
              <Badge :variant="provider.enabled ? 'default' : 'outline'">{{ provider.enabled ? t('common.active') : t('common.inactive') }}</Badge>
              <Badge variant="outline" class="text-xs">P{{ provider.priority }}</Badge>
            </div>
            <p class="text-xs text-slate-500">{{ provider.model_name }} · {{ provider.base_url }}</p>
            <p class="text-xs text-slate-500">
              {{ t('settings.aiProviders.quota') }}: {{ provider.quota_limit ? `${provider.quota_used}/${provider.quota_limit}` : t('settings.aiProviders.unlimited') }}
            </p>
          </div>
          <div class="flex gap-1">
            <Button variant="ghost" size="sm" @click="handleResetQuota(provider.id)"><RotateCcw class="h-4 w-4" /></Button>
            <Button variant="ghost" size="sm" @click="handleEdit(provider)"><Pencil class="h-4 w-4" /></Button>
            <Button variant="ghost" size="sm" @click="handleDelete(provider.id)"><Trash2 class="h-4 w-4" /></Button>
          </div>
        </div>
      </div>

      <div v-if="showForm" class="mt-4 rounded-lg border border-sky-200 bg-sky-50/50 p-4 space-y-4">
        <h4 class="font-medium text-sm">{{ editingId ? t('settings.aiProviders.editTitle') : t('settings.aiProviders.addTitle') }}</h4>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="grid gap-2"><Label>{{ t('settings.aiProviders.name') }}</Label><Input v-model="form.name" :placeholder="t('settings.aiProviders.namePlaceholder')" /></div>
          <div class="grid gap-2"><Label>{{ t('settings.aiProviders.modelName') }}</Label><Input v-model="form.model_name" placeholder="gpt-4o" /></div>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
          <div class="grid gap-2"><Label>Base URL</Label><Input v-model="form.base_url" placeholder="https://api.openai.com/v1" /></div>
          <div class="grid gap-2"><Label>API Key</Label><Input v-model="form.api_key" type="password" :placeholder="editingId ? t('settings.aiProviders.apiKeyKeep') : 'sk-...'" /></div>
        </div>
        <div class="grid gap-4 md:grid-cols-3">
          <div class="grid gap-2"><Label>{{ t('settings.aiProviders.proxyUrl') }}</Label><Input v-model="form.proxy_url" placeholder="http://127.0.0.1:7890" /></div>
          <div class="grid gap-2"><Label>{{ t('settings.aiProviders.quotaLimit') }}</Label><Input v-model.number="form.quota_limit" type="number" :placeholder="t('settings.aiProviders.quotaLimitPlaceholder')" /></div>
          <div class="grid gap-2"><Label>{{ t('settings.aiProviders.priority') }}</Label><Input v-model.number="form.priority" type="number" placeholder="0" /></div>
        </div>
        <div class="flex items-center gap-3">
          <Switch :model-value="!!form.enabled" @update:model-value="(v) => form.enabled = !!v" />
          <Label>{{ t('settings.aiProviders.enabled') }}</Label>
        </div>
        <div class="flex gap-2">
          <Button size="sm" @click="handleSubmit">{{ editingId ? t('common.save') : t('settings.aiProviders.add') }}</Button>
          <Button size="sm" variant="outline" @click="handleCancel">{{ t('common.cancel') }}</Button>
        </div>
      </div>
</CardContent>
  </Card>
</template>
