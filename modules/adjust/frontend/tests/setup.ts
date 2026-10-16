import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';
afterEach(cleanup);
window.scrollTo = vi.fn();
HTMLElement.prototype.scrollIntoView = vi.fn();
