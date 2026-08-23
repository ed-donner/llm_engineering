<template>
  <div class="bg-primary text-white">
    <UContainer>
      <div class="flex items-center h-16">
        <EvsLogo />
        <div class="flex-1" />
        <!-- Mobile menu button -->
        <div class="md:hidden">
          <UButton
            variant="ghost"
            color="white"
            aria-label="Open menu"
            :padded="false"
            icon="i-mdi-menu"
            @click="showMobileMenu"
          />
        </div>
        <!-- Desktop menu -->
        <div class="hidden md:flex items-center gap-2">
          <UButton to="/privacy" variant="ghost" color="white">Privacy</UButton>
          <UButton to="/contact" variant="ghost" color="white">Contact</UButton>
          <UButton to="/auth/login" color="white" variant="ghost">Sign in</UButton>
          <UButton
            to="/auth/signup"
            variant="ghost"
            color="white"
            class="border border-white rounded-full"
          >
            Create Account
          </UButton>
        </div>
      </div>
    </UContainer>

    <!-- Fullscreen mobile navigation -->
    <UModal
      v-model="navOpened"
      prevent-close
      :ui="{
        container: 'items-start',
        base: 'h-screen w-screen m-0 rounded-none',
        padding: 'p-0',
        overlay: { background: 'bg-black/50' }
      }"
    >
      <div class="bg-white h-screen w-screen relative">
        <div class="bg-primary text-white">
          <UContainer>
            <div class="flex items-center h-16">
              <EvsLogo />
              <div class="flex-1" />
              <UButton
                variant="ghost"
                color="white"
                aria-label="Close menu"
                :padded="false"
                icon="i-mdi-close-circle-outline"
                @click="closeMenu"
              />
            </div>
          </UContainer>
        </div>

        <div class="absolute inset-x-0 top-16 bottom-0 overflow-y-auto text-left">
          <UList class="divide-y divide-gray-200">
            <UListItem to="/privacy" title="Privacy">
              <template #trailing>
                <UIcon name="i-mdi-chevron-right" />
              </template>
            </UListItem>
            <UListItem to="/contact" title="Contact">
              <template #trailing>
                <UIcon name="i-mdi-chevron-right" />
              </template>
            </UListItem>
            <UListItem to="/auth/login" title="Login">
              <template #trailing>
                <UIcon name="i-mdi-chevron-right" />
              </template>
            </UListItem>
            <UListItem to="/auth/signup" title="Sign up">
              <template #trailing>
                <UIcon name="i-mdi-chevron-right" />
              </template>
            </UListItem>
          </UList>
        </div>
      </div>
    </UModal>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const navOpened = ref<boolean>(false)

const showMobileMenu = () => {
  navOpened.value = true
}
const closeMenu = () => {
  navOpened.value = false
}
</script>