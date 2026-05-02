<template>
  <div class="border border-gray-300 rounded-lg overflow-hidden">
    <div class="bg-gray-50 border-b border-gray-200 px-3 py-2 flex flex-wrap gap-1 items-center">
      <button
        :class="editor?.isActive('bold') ? 'bg-gray-200' : 'hover:bg-gray-200'"
        class="px-2.5 py-1.5 rounded text-sm font-bold transition-colors"
        title="加粗"
        @click="editor?.chain().focus().toggleBold().run()"
      >
        <strong>B</strong>
      </button>
      <button
        :class="editor?.isActive('italic') ? 'bg-gray-200' : 'hover:bg-gray-200'"
        class="px-2.5 py-1.5 rounded text-sm italic transition-colors"
        title="斜体"
        @click="editor?.chain().focus().toggleItalic().run()"
      >
        <em>I</em>
      </button>
      <span class="w-px h-5 bg-gray-300 mx-1" />
      <button
        :class="editor?.isActive('heading', { level: 2 }) ? 'bg-gray-200' : 'hover:bg-gray-200'"
        class="px-2.5 py-1.5 rounded text-sm font-semibold transition-colors"
        title="二级标题"
        @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()"
      >
        H2
      </button>
      <button
        :class="editor?.isActive('heading', { level: 3 }) ? 'bg-gray-200' : 'hover:bg-gray-200'"
        class="px-2.5 py-1.5 rounded text-sm font-semibold transition-colors"
        title="三级标题"
        @click="editor?.chain().focus().toggleHeading({ level: 3 }).run()"
      >
        H3
      </button>
      <span class="w-px h-5 bg-gray-300 mx-1" />
      <button
        :class="editor?.isActive('bulletList') ? 'bg-gray-200' : 'hover:bg-gray-200'"
        class="px-2.5 py-1.5 rounded text-sm transition-colors"
        title="无序列表"
        @click="editor?.chain().focus().toggleBulletList().run()"
      >
        ≡
      </button>
      <button
        :class="editor?.isActive('orderedList') ? 'bg-gray-200' : 'hover:bg-gray-200'"
        class="px-2.5 py-1.5 rounded text-sm transition-colors"
        title="有序列表"
        @click="editor?.chain().focus().toggleOrderedList().run()"
      >
        1.
      </button>
      <span class="w-px h-5 bg-gray-300 mx-1" />
      <button
        class="px-2.5 py-1.5 rounded text-sm hover:bg-gray-200 transition-colors"
        title="插入表格"
        @click="editor?.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()"
      >
        表格
      </button>
      <button
        class="px-2.5 py-1.5 rounded text-sm hover:bg-gray-200 transition-colors"
        title="插入图片"
        @click="handleImageUpload"
      >
        🖼 图片
      </button>
      <button
        :class="editor?.isActive('link') ? 'bg-gray-200' : 'hover:bg-gray-200'"
        class="px-2.5 py-1.5 rounded text-sm transition-colors"
        title="插入链接"
        @click="handleAddLink"
      >
        🔗
      </button>
      <button
        :class="editor?.isActive('blockquote') ? 'bg-gray-200' : 'hover:bg-gray-200'"
        class="px-2.5 py-1.5 rounded text-sm transition-colors"
        title="引用"
        @click="editor?.chain().focus().toggleBlockquote().run()"
      >
        "
      </button>
      <span class="w-px h-5 bg-gray-300 mx-1" />
      <button
        class="px-2.5 py-1.5 rounded text-sm hover:bg-gray-200 transition-colors"
        title="撤销"
        @click="editor?.chain().focus().undo().run()"
      >
        ↩
      </button>
      <button
        class="px-2.5 py-1.5 rounded text-sm hover:bg-gray-200 transition-colors"
        title="重做"
        @click="editor?.chain().focus().redo().run()"
      >
        ↪
      </button>
      <input
        ref="fileInput"
        type="file"
        accept="image/*"
        class="hidden"
        @change="onFileSelected"
      >
    </div>
    <div
      class="prose prose-sm max-w-none p-4 min-h-[300px]"
      @drop.prevent="onDrop"
      @dragover.prevent
      @paste="onPaste"
    >
      <editor-content :editor="editor" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import { Table } from '@tiptap/extension-table'
import { TableRow } from '@tiptap/extension-table-row'
import { TableCell } from '@tiptap/extension-table-cell'
import { TableHeader } from '@tiptap/extension-table-header'

const props = defineProps<{
  modelValue: string
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const fileInput = ref<HTMLInputElement>()

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit.configure({
      heading: { levels: [2, 3] },
    }),
    Table.configure({ resizable: false }),
    TableRow,
    TableCell,
    TableHeader,
    Image.configure({
      inline: true,
      allowBase64: false,
    }),
    Link.configure({
      openOnClick: true,
      HTMLAttributes: { rel: 'noopener noreferrer', target: '_blank' },
    }),
    Placeholder.configure({
      placeholder: props.placeholder || '开始编写内容...',
    }),
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  },
})

watch(() => props.modelValue, (val) => {
  if (editor.value && val !== editor.value.getHTML()) {
    editor.value.commands.setContent(val, false)
  }
})

async function uploadImage(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const token = localStorage.getItem('admin_token')
  const res = await fetch('/api/v1/content/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData,
  })
  if (!res.ok) throw new Error('上传失败')
  const data = await res.json()
  return data.url
}

async function handleImageUpload() {
  fileInput.value?.click()
}

async function onFileSelected(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  try {
    const url = await uploadImage(file)
    editor.value?.chain().focus().setImage({ src: url }).run()
  } catch (e) {
    console.error('图片上传失败:', e)
  }
  target.value = ''
}

async function onDrop(event: DragEvent) {
  const files = event.dataTransfer?.files
  if (!files?.length) return
  for (const file of Array.from(files)) {
    if (file.type.startsWith('image/')) {
      try {
        const url = await uploadImage(file)
        editor.value?.chain().focus().setImage({ src: url }).run()
      } catch (e) {
        console.error('图片上传失败:', e)
      }
    }
  }
}

async function onPaste(event: ClipboardEvent) {
  const items = event.clipboardData?.items
  if (!items) return
  for (const item of Array.from(items)) {
    if (item.type.startsWith('image/')) {
      event.preventDefault()
      const file = item.getAsFile()
      if (file) {
        try {
          const url = await uploadImage(file)
          editor.value?.chain().focus().setImage({ src: url }).run()
        } catch (e) {
          console.error('图片上传失败:', e)
        }
      }
    }
  }
}

async function handleAddLink() {
  const url = prompt('请输入链接地址:')
  if (url) {
    editor.value?.chain().focus().setLink({ href: url }).run()
  }
}

onBeforeUnmount(() => editor.value?.destroy())
</script>
