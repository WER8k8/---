<template>
  <div class="min-h-screen bg-gray-50 py-12">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="bg-white rounded-lg shadow-md p-8">
        <h1 class="text-3xl font-bold text-gray-900 mb-6">
          {{ t('privacy.title') }}
        </h1>

        <div class="prose max-w-none">
          <p class="text-gray-600 mb-4">
            {{ t('privacy.lastUpdated') }}
          </p>

          <section class="mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-3">
              {{ t('privacy.section1Title') }}
            </h2>
            <p class="text-gray-700 leading-relaxed">
              {{ t('privacy.section1Content') }}
            </p>
            <ul class="list-disc list-inside text-gray-700 mt-2 space-y-1 ml-4">
              <li>{{ t('privacy.section1Item1') }}</li>
              <li>{{ t('privacy.section1Item2') }}</li>
              <li>{{ t('privacy.section1Item3') }}</li>
              <li>{{ t('privacy.section1Item4') }}</li>
              <li>{{ t('privacy.section1Item5') }}</li>
            </ul>
          </section>

          <section class="mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-3">
              {{ t('privacy.section2Title') }}
            </h2>
            <p class="text-gray-700 leading-relaxed">
              {{ t('privacy.section2Content') }}
            </p>
            <ul class="list-disc list-inside text-gray-700 mt-2 space-y-1 ml-4">
              <li>{{ t('privacy.section2Item1') }}</li>
              <li>{{ t('privacy.section2Item2') }}</li>
              <li>{{ t('privacy.section2Item3') }}</li>
              <li>{{ t('privacy.section2Item4') }}</li>
              <li>{{ t('privacy.section2Item5') }}</li>
            </ul>
          </section>

          <section class="mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-3">
              {{ t('privacy.section3Title') }}
            </h2>
            <p class="text-gray-700 leading-relaxed">
              {{ t('privacy.section3Content') }}
            </p>
            <ul class="list-disc list-inside text-gray-700 mt-2 space-y-1 ml-4">
              <li>{{ t('privacy.section3Item1') }}</li>
              <li>{{ t('privacy.section3Item2') }}</li>
              <li>{{ t('privacy.section3Item3') }}</li>
              <li>{{ t('privacy.section3Item4') }}</li>
            </ul>
          </section>

          <section class="mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-3">
              {{ t('privacy.section4Title') }}
            </h2>
            <p class="text-gray-700 leading-relaxed">
              {{ t('privacy.section4Content') }}
            </p>
            <ul class="list-disc list-inside text-gray-700 mt-2 space-y-1 ml-4">
              <li>{{ t('privacy.section4Item1') }}</li>
              <li>{{ t('privacy.section4Item2') }}</li>
              <li>{{ t('privacy.section4Item3') }}</li>
              <li>{{ t('privacy.section4Item4') }}</li>
            </ul>
          </section>

          <section class="mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-3">
              {{ t('privacy.section5Title') }}
            </h2>
            <p class="text-gray-700 leading-relaxed">
              {{ t('privacy.section5Content') }}
            </p>
            <ul class="list-disc list-inside text-gray-700 mt-2 space-y-1 ml-4">
              <li>{{ t('privacy.section5Item1') }}</li>
              <li>{{ t('privacy.section5Item2') }}</li>
              <li>{{ t('privacy.section5Item3') }}</li>
              <li>{{ t('privacy.section5Item4') }}</li>
            </ul>
          </section>

          <section class="mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-3">
              {{ t('privacy.section6Title') }}
            </h2>
            <p class="text-gray-700 leading-relaxed">
              {{ t('privacy.section6Content') }}
            </p>
            <ul class="list-disc list-inside text-gray-700 mt-2 space-y-1 ml-4">
              <li>{{ t('privacy.section6Item1') }}</li>
              <li>{{ t('privacy.section6Item2') }}</li>
              <li>{{ t('privacy.section6Item3') }}</li>
              <li>{{ t('privacy.section6Item4') }}</li>
            </ul>
          </section>

          <section class="mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-3">
              {{ t('privacy.section7Title') }}
            </h2>
            <p class="text-gray-700 leading-relaxed">
              {{ t('privacy.section7Content') }}
            </p>
            <ul class="list-disc list-inside text-gray-700 mt-2 space-y-1 ml-4">
              <li>{{ t('privacy.section7Item1') }}</li>
              <li>{{ t('privacy.section7Item2') }}</li>
              <li>{{ t('privacy.section7Item3') }}</li>
              <li>{{ t('privacy.section7Item4') }}</li>
            </ul>
          </section>

          <section class="mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-3">
              {{ t('privacy.section8Title') }}
            </h2>
            <p class="text-gray-700 leading-relaxed">
              {{ t('privacy.section8Content') }}
            </p>
          </section>

          <section class="mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-3">
              {{ t('privacy.section9Title') }}
            </h2>
            <p class="text-gray-700 leading-relaxed">
              {{ t('privacy.section9Content') }}
            </p>
          </section>

          <section class="mb-6">
            <h2 class="text-xl font-semibold text-gray-800 mb-3">
              {{ t('privacy.section10Title') }}
            </h2>
            <p class="text-gray-700 leading-relaxed">
              {{ t('privacy.section10Content') }}
            </p>
            <p class="text-gray-700 mt-2">
              {{ t('privacy.section10Email') }}<br>
              {{ t('privacy.section10Phone') }}
            </p>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

useHead({
  title: t('privacy.seoTitle'),
  meta: [{ name: 'description', content: t('privacy.seoDescription') }],
});
</script>
