import type { Meta, StoryObj } from '@storybook/react';
import { JobTracker } from './JobTracker';

const meta: Meta<typeof JobTracker> = {
  title: 'Components/JobTracker',
  component: JobTracker,
};

export default meta;
type Story = StoryObj<typeof JobTracker>;

export const InProgress: Story = {
  args: {
    currentStepId: 'CODE_EMBEDDING_INGESTION',
    status: 'IN_PROGRESS',
  },
};

export const Failed: Story = {
  args: {
    currentStepId: 'TEST_EXECUTION',
    status: 'FAILED',
  },
};

export const Blocked: Story = {
  args: {
    currentStepId: 'IMPLEMENTATION_START',
    status: 'BLOCKED',
  },
};
