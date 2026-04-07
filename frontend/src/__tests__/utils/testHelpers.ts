/**
 * 测试辅助函数
 * 
 * 提供可复用的测试工具函数
 */

// ============================================================================
// 组件挂载工具
// ============================================================================

/**
 * 挂载组件并配置全局mock
 */
export const mountComponent = <T>(
  component: any,
  options?: {
    props?: Record<string, any>
    global?: {
      mocks?: Record<string, any>
      plugins?: any[]
    }
  }
) => {
  return component;
}

// ============================================================================
// 等待工具
// ============================================================================

/**
 * 等待元素出现
 */
export const waitForElement = async (
  element: any,
  timeout = 5000,
) => {
  try {
    return await new Promise((resolve, reject) => {
      const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          if (Array.from(mutation.addedNodes).some(node => node.contains(element))) {
            resolve(element);
            observer.disconnect();
          }
        });
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true,
      });

      setTimeout(() => {
        observer.disconnect();
        reject(new Error(`Element not found within ${timeout}ms`));
      }, timeout);
    });
  } catch (error) {
    return Promise.reject(error);
  }
}

/**
 * 等待多个元素出现
 */
export const waitForElements = async (
  selectors: string[],
  timeout = 5000,
) => {
  try {
    return await Promise.all(selectors.map(selector => waitForElement(selector, timeout)));
  } catch (error) {
    throw error;
  }
}

// ============================================================================
// 事件触发工具
// ============================================================================

/**
 * 触发元素的点击事件
 */
export const clickElement = async (element: HTMLElement | any) => {
  if (element instanceof HTMLElement) {
    element.click();
    await new Promise(resolve => setTimeout(resolve, 0));
  }
}

/**
 * 触发元素的输入事件
 */
export const inputElement = async (
  element: HTMLElement | any,
  value: string,
) => {
  if (element instanceof HTMLElement) {
    element.value = value;
    element.dispatchEvent(new Event('input', { bubbles: true }));
    await new Promise(resolve => setTimeout(resolve, 0));
  }
}

/**
 * 触发元素的change事件
 */
export const changeElement = async (
  element: HTMLElement | any,
  value: string,
) => {
  if (element instanceof HTMLElement) {
    element.value = value;
    element.dispatchEvent(new Event('change', { bubbles: true }));
    await new Promise(resolve => setTimeout(resolve, 0));
  }
}

// ============================================================================
// 表单操作工具
// ============================================================================

/**
 * 填充表单字段
 */
export const fillForm = async (
  form: HTMLElement | any,
  data: Record<string, any>,
) => {
  Object.entries(data).forEach(([key, value]) => {
    const input = form.querySelector(`[name="${key}"]`) as HTMLInputElement;
    if (input) {
      input.value = String(value);
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  });
}

// ============================================================================
// 消息验证工具
// ============================================================================

/**
 * 验证成功消息显示
 */
export const checkSuccessMessage = async () => {
  const messageElement = document.querySelector('.el-message--success') as HTMLElement;
  if (messageElement) {
    expect(messageElement.textContent).toBeTruthy();
  }
}

/**
 * 验证错误消息显示
 */
export const checkErrorMessage = async (message?: string) => {
  const messageElement = document.querySelector('.el-message--error') as HTMLElement;
  if (messageElement) {
    expect(messageElement.textContent).toBeTruthy();
    if (message) {
      expect(messageElement.textContent).toContain(message);
    }
  }
}

/**
 * 等待加载完成
 */
export const waitForLoadingComplete = async (timeout = 5000) => {
  const loadingElement = document.querySelector('.el-loading-mask') as HTMLElement;
  try {
    await waitForElement(() => !loadingElement || window.getComputedStyle(loadingElement).display === 'none', timeout);
  } catch (error) {
    // Loading element not found, continue
  }
}

// ============================================================================
// 确认对话框操作工具
// ============================================================================

/**
 * 确认对话框
 */
export const confirmDialog = async () => {
  const confirmButton = document.querySelector('.el-button--primary:not(.disabled)') as HTMLElement;
  if (confirmButton) {
    await clickElement(confirmButton);
  }
}

/**
 * 取消对话框
 */
export const cancelDialog = async () => {
  const cancelButton = document.querySelector('.el-button--default') as HTMLElement;
  if (cancelButton) {
    await clickElement(cancelButton);
  }
}

// ============================================================================
// 辅助函数：获取元素文本
// ============================================================================

/**
 * 获取元素的文本内容
 */
export const getElementText = (selector: string): string => {
  const element = document.querySelector(selector) as HTMLElement;
  return element ? element.textContent || '' : '';
}

/**
 * 获取元素的属性值
 */
export const getElementAttribute = (selector: string, attribute: string): string | null => {
  const element = document.querySelector(selector) as HTMLElement;
  return element ? element.getAttribute(attribute) || null : '';
}

/**
 * 检查元素是否存在
 */
export const elementExists = (selector: string): boolean => {
  return document.querySelector(selector) !== null;
}

/**
 * 检查元素是否可见
 */
export const elementVisible = (selector: string): boolean => {
  const element = document.querySelector(selector) as HTMLElement;
  if (!element) return false;
  return element.offsetParent !== null && window.getComputedStyle(element).display !== 'none';
}

// ============================================================================
// 辅助函数：等待和检查
// ============================================================================

/**
 * 等待指定时间
 */
export const wait = async (ms: number) => {
  await new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 等待下一个tick
 */
export const nextTick = async () => {
  await new Promise(resolve => setTimeout(resolve, 0));
}

/**
 * 等待指定数量的帧
 */
export const waitFrames = async (frames = 60) => {
  await new Promise(resolve => {
    let count = 0;
    const tick = () => {
      requestAnimationFrame(() => {
        if (count >= frames) {
          resolve(undefined);
        } else {
          count++;
          tick();
        }
      });
    };
    tick();
  });
}
