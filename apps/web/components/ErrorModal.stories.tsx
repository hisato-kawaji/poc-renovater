import type { Meta, StoryObj } from '@storybook/react';
import { ErrorModal } from './ErrorModal';

const meta: Meta<typeof ErrorModal> = {
  title: 'Components/ErrorModal',
  component: ErrorModal,
};

export default meta;
type Story = StoryObj<typeof ErrorModal>;

export const Default: Story = {
  args: {
    isOpen: true,
    errorMessage: "Error: Process exited with code 1\n  at run (script.js:12:5)",
  },
};
