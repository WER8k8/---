/**
 * Mobile Interaction Utilities
 * Enhanced mobile-specific interactions and gestures
 */

import { ref, computed, onMounted, onUnmounted } from 'vue';

/**
 * Composable for mobile-specific touch interactions
 */
export function useMobileInteractions() {
  // Touch start position
  const touchStartX = ref(0);
  const touchStartY = ref(0);
  const touchStartTime = ref(0);

  // Swipe state
  const isSwiping = ref(false);
  const swipeDirection = ref<'left' | 'right' | 'up' | 'down' | null>(null);
  const swipeDistance = ref({ x: 0, y: 0 });

  // Minimum swipe distance to register (in pixels)
  const minSwipeDistance = 50;
  // Maximum time for a swipe (in milliseconds)
  const maxSwipeTime = 500;

  // Handle touch start
  const handleTouchStart = (e: TouchEvent) => {
    const touch = e.touches[0];
    touchStartX.value = touch.clientX;
    touchStartY.value = touch.clientY;
    touchStartTime.value = Date.now();
    isSwiping.value = true;
    swipeDirection.value = null;
    swipeDistance.value = { x: 0, y: 0 };
  };

  // Handle touch move
  const handleTouchMove = (e: TouchEvent) => {
    if (!isSwiping.value) return;

    const touch = e.touches[0];
    const currentX = touch.clientX;
    const currentY = touch.clientY;

    swipeDistance.value = {
      x: currentX - touchStartX.value,
      y: currentY - touchStartY.value,
    };
  };

  // Handle touch end
  const handleTouchEnd = () => {
    if (!isSwiping.value) return;

    const elapsedTime = Date.now() - touchStartTime.value;

    // Only register swipe if it happened quickly enough
    if (elapsedTime <= maxSwipeTime) {
      const { x: dx, y: dy } = swipeDistance.value;
      const absDx = Math.abs(dx);
      const absDy = Math.abs(dy);

      // Determine swipe direction
      if (absDx > minSwipeDistance || absDy > minSwipeDistance) {
        if (absDx > absDy) {
          swipeDirection.value = dx > 0 ? 'right' : 'left';
        } else {
          swipeDirection.value = dy > 0 ? 'down' : 'up';
        }
      }
    }

    isSwiping.value = false;
  };

  // Reset swipe state
  const resetSwipe = () => {
    swipeDirection.value = null;
    swipeDistance.value = { x: 0, y: 0 };
  };

  // Touch event handlers for swipe detection
  const swipeHandlers = {
    onTouchStart: handleTouchStart,
    onTouchMove: handleTouchMove,
    onTouchEnd: handleTouchEnd,
  };

  return {
    isSwiping,
    swipeDirection,
    swipeDistance,
    resetSwipe,
    swipeHandlers,
    minSwipeDistance,
  };
}

/**
 * Composable for touch feedback effects
 */
export function useTouchFeedback() {
  // Active touch element
  const activeElement = ref<string | null>(null);

  // Touch ripple state
  const ripples = ref<
    Array<{
      id: number;
      x: number;
      y: number;
      elementId: string;
    }>
  >([]);

  let rippleIdCounter = 0;

  // Add touch ripple effect
  const addRipple = (elementId: string, event: TouchEvent | MouseEvent) => {
    const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();

    let clientX: number;
    let clientY: number;

    if ('touches' in event) {
      clientX = event.touches[0].clientX;
      clientY = event.touches[0].clientY;
    } else {
      clientX = event.clientX;
      clientY = event.clientY;
    }

    const x = clientX - rect.left;
    const y = clientY - rect.top;

    const ripple = {
      id: rippleIdCounter++,
      x,
      y,
      elementId,
    };

    ripples.value.push(ripple);

    // Remove ripple after animation completes
    setTimeout(() => {
      ripples.value = ripples.value.filter((r) => r.id !== ripple.id);
    }, 600);
  };

  // Set active element for visual feedback
  const setActiveElement = (elementId: string | null) => {
    activeElement.value = elementId;
  };

  return {
    activeElement,
    ripples,
    addRipple,
    setActiveElement,
  };
}

/**
 * Composable for mobile smooth scrolling
 */
export function useMobileScrolling() {
  // Scroll position
  const scrollY = ref(0);
  const scrollX = ref(0);

  // Scroll direction
  const scrollDirection = ref<'up' | 'down' | 'left' | 'right' | null>(null);

  // Previous scroll position
  const prevScrollY = ref(0);
  const prevScrollX = ref(0);

  // Handle scroll event
  const handleScroll = () => {
    if (process.client) {
      scrollY.value = window.scrollY;
      scrollX.value = window.scrollX;

      // Determine scroll direction
      if (scrollY.value > prevScrollY.value) {
        scrollDirection.value = 'down';
      } else if (scrollY.value < prevScrollY.value) {
        scrollDirection.value = 'up';
      }

      if (scrollX.value > prevScrollX.value) {
        scrollDirection.value = 'right';
      } else if (scrollX.value < prevScrollX.value) {
        scrollDirection.value = 'left';
      }

      prevScrollY.value = scrollY.value;
      prevScrollX.value = scrollX.value;
    }
  };

  // Smooth scroll to element
  const smoothScrollTo = (elementId: string, offset = 0) => {
    if (process.client) {
      const element = document.getElementById(elementId);
      if (element) {
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.scrollY + offset;

        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth',
        });
      }
    }
  };

  // Smooth scroll to top
  const scrollToTop = () => {
    if (process.client) {
      window.scrollTo({
        top: 0,
        behavior: 'smooth',
      });
    }
  };

  // Check if element is in viewport
  const isInViewport = (elementId: string, offset = 0): boolean => {
    if (process.client) {
      const element = document.getElementById(elementId);
      if (!element) return false;

      const rect = element.getBoundingClientRect();
      return (
        rect.top >= 0 - offset &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) + offset &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
      );
    }
    return false;
  };

  // Setup scroll listener
  onMounted(() => {
    if (process.client) {
      window.addEventListener('scroll', handleScroll, { passive: true });
      scrollY.value = window.scrollY;
      scrollX.value = window.scrollX;
      prevScrollY.value = scrollY.value;
      prevScrollX.value = scrollX.value;
    }
  });

  onUnmounted(() => {
    if (process.client) {
      window.removeEventListener('scroll', handleScroll);
    }
  });

  return {
    scrollY,
    scrollX,
    scrollDirection,
    smoothScrollTo,
    scrollToTop,
    isInViewport,
  };
}

/**
 * Composable for mobile gesture support
 */
export function useMobileGestures() {
  // Pinch/zoom state
  const isPinching = ref(false);
  const initialPinchDistance = ref(0);
  const currentPinchDistance = ref(0);

  // Rotation state
  const isRotating = ref(false);
  const initialRotation = ref(0);
  const currentRotation = ref(0);

  // Calculate distance between two touches
  const getDistance = (touch1: Touch, touch2: Touch): number => {
    const dx = touch2.clientX - touch1.clientX;
    const dy = touch2.clientY - touch1.clientY;
    return Math.sqrt(dx * dx + dy * dy);
  };

  // Calculate angle between two touches
  const getAngle = (touch1: Touch, touch2: Touch): number => {
    const dx = touch2.clientX - touch1.clientX;
    const dy = touch2.clientY - touch1.clientY;
    return Math.atan2(dy, dx) * (180 / Math.PI);
  };

  // Handle gesture start
  const handleGestureStart = (e: TouchEvent) => {
    if (e.touches.length === 2) {
      initialPinchDistance.value = getDistance(e.touches[0], e.touches[1]);
      initialRotation.value = getAngle(e.touches[0], e.touches[1]);
      isPinching.value = true;
      isRotating.value = true;
    }
  };

  // Handle gesture change
  const handleGestureChange = (e: TouchEvent) => {
    if (e.touches.length === 2 && (isPinching.value || isRotating.value)) {
      currentPinchDistance.value = getDistance(e.touches[0], e.touches[1]);
      currentRotation.value = getAngle(e.touches[0], e.touches[1]);

      // Prevent default scrolling during gesture
      e.preventDefault();
    }
  };

  // Handle gesture end
  const handleGestureEnd = () => {
    isPinching.value = false;
    isRotating.value = false;
  };

  // Calculate scale factor
  const scale = computed(() => {
    if (initialPinchDistance.value === 0) return 1;
    return currentPinchDistance.value / initialPinchDistance.value;
  });

  // Calculate rotation delta
  const rotationDelta = computed(() => {
    return currentRotation.value - initialRotation.value;
  });

  // Gesture event handlers
  const gestureHandlers = {
    onTouchStart: handleGestureStart,
    onTouchMove: handleGestureChange,
    onTouchEnd: handleGestureEnd,
  };

  return {
    isPinching,
    isRotating,
    scale,
    rotationDelta,
    gestureHandlers,
  };
}

/**
 * Composable for mobile-friendly form interactions
 */
export function useMobileForm() {
  // Focused input state
  const focusedInput = ref<string | null>(null);

  // Virtual keyboard state
  const isKeyboardOpen = ref(false);
  const keyboardHeight = ref(0);

  // Handle input focus
  const handleInputFocus = (inputId: string) => {
    focusedInput.value = inputId;
  };

  // Handle input blur
  const handleInputBlur = () => {
    focusedInput.value = null;
  };

  // Handle keyboard visibility change (iOS)
  const handleResize = () => {
    if (process.client) {
      const viewportHeight = window.innerHeight;
      const documentHeight = document.documentElement.clientHeight;

      // Detect keyboard by comparing heights
      const diff = documentHeight - viewportHeight;
      if (diff > 100) {
        isKeyboardOpen.value = true;
        keyboardHeight.value = diff;
      } else {
        isKeyboardOpen.value = false;
        keyboardHeight.value = 0;
      }
    }
  };

  // Scroll to focused input if it's hidden by keyboard
  const scrollToInput = (inputId: string) => {
    if (process.client) {
      const input = document.getElementById(inputId);
      if (input && isKeyboardOpen.value) {
        setTimeout(() => {
          input.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 100);
      }
    }
  };

  // Setup resize listener for keyboard detection
  onMounted(() => {
    if (process.client) {
      window.addEventListener('resize', handleResize);
      handleResize(); // Initial check
    }
  });

  onUnmounted(() => {
    if (process.client) {
      window.removeEventListener('resize', handleResize);
    }
  });

  return {
    focusedInput,
    isKeyboardOpen,
    keyboardHeight,
    handleInputFocus,
    handleInputBlur,
    scrollToInput,
  };
}
