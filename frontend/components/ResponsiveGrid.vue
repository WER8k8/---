<template>
  <div
    class="grid gap-4 sm:gap-6 lg:gap-8"
    :class="gridClass"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
type Columns = 1 | 2 | 3 | 4 | 5 | 6

interface GridProps {
  // Columns for each breakpoint
  cols?: {
    xs?: Columns
    sm?: Columns
    md?: Columns
    lg?: Columns
    xl?: Columns
  }
  
  // Gap size
  gap?: 'none' | 'sm' | 'md' | 'lg' | 'xl'
  
  // Item minimum width (for auto-fit grids)
  minItemWidth?: string
}

const props = withDefaults(defineProps<GridProps>(), {
  gap: 'md',
  minItemWidth: '280px'
})

// Generate grid class based on props
const gridClass = computed(() => {
  const { cols, gap, minItemWidth } = props
  
  // Gap classes
  const gapClasses = {
    none: 'gap-0',
    sm: 'gap-4',
    md: 'gap-6',
    lg: 'gap-8',
    xl: 'gap-12'
  }
  
  // If using auto-fit grid (minItemWidth specified)
  if (minItemWidth && !cols) {
    return `${gapClasses[gap]} grid-cols-[repeat(auto-fill,minmax(${minItemWidth},1fr))]`
  }
  
  // Default responsive columns
  const defaultCols = {
    xs: cols?.xs || 1,
    sm: cols?.sm || 2,
    md: cols?.md || 3,
    lg: cols?.lg || 4,
    xl: cols?.xl || 4
  }
  
  return [
    gapClasses[gap],
    `grid-cols-${defaultCols.xs}`,
    `sm:grid-cols-${defaultCols.sm}`,
    `md:grid-cols-${defaultCols.md}`,
    `lg:grid-cols-${defaultCols.lg}`,
    `xl:grid-cols-${defaultCols.xl}`
  ].join(' ')
})
</script>
