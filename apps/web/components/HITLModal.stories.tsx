import type { Meta, StoryObj } from '@storybook/react';
import { HITLModal } from './HITLModal';

const meta: Meta<typeof HITLModal> = {
  title: 'Components/HITLModal',
  component: HITLModal,
};

export default meta;
type Story = StoryObj<typeof HITLModal>;

export const JustApproval: Story = {
  args: {
    isOpen: true,
    blockedReason: "Please review the generated code and approve the Pull Request.",
    requiresEnvVars: false,
  },
};

export const NeedsEnvVars: Story = {
  args: {
    isOpen: true,
    blockedReason: "Sandbox requires sensitive environment variables before provisioning.",
    requiresEnvVars: true,
  },
};
