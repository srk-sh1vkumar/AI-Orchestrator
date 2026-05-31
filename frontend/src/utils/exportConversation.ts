/**
 * Export Conversation Utility
 *
 * Enhancement 022: Export conversations in multiple formats
 */

import axios from 'axios';

export type ExportFormat = 'markdown' | 'json' | 'pdf';

interface ExportOptions {
  conversationId: string;
  format: ExportFormat;
  filename?: string;
}

/**
 * Export a conversation in the specified format
 */
export async function exportConversation({
  conversationId,
  format,
  filename,
}: ExportOptions): Promise<void> {
  try {
    // Fetch export data from API
    const response = await axios.get(
      `http://localhost:8000/api/conversations/${conversationId}/export`,
      {
        params: { format },
        responseType: 'blob', // Important for file downloads
      }
    );

    // Determine filename if not provided
    const defaultFilename = `conversation_${conversationId}.${getFileExtension(
      format
    )}`;
    const downloadFilename = filename || defaultFilename;

    // Create blob URL and trigger download
    const blob = new Blob([response.data], {
      type: getContentType(format),
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = downloadFilename;
    document.body.appendChild(link);
    link.click();

    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Failed to export conversation:', error);
    throw new Error(`Failed to export conversation as ${format}`);
  }
}

/**
 * Get file extension for format
 */
function getFileExtension(format: ExportFormat): string {
  switch (format) {
    case 'markdown':
      return 'md';
    case 'json':
      return 'json';
    case 'pdf':
      return 'html'; // HTML for PDF conversion
    default:
      return 'txt';
  }
}

/**
 * Get MIME content type for format
 */
function getContentType(format: ExportFormat): string {
  switch (format) {
    case 'markdown':
      return 'text/markdown';
    case 'json':
      return 'application/json';
    case 'pdf':
      return 'text/html';
    default:
      return 'text/plain';
  }
}

/**
 * Convert HTML to PDF using browser print API
 * (for client-side PDF generation)
 */
export async function convertHtmlToPdf(htmlContent: string, filename: string): Promise<void> {
  // Open HTML in new window and trigger print
  const printWindow = window.open('', '_blank');
  if (!printWindow) {
    throw new Error('Failed to open print window');
  }

  printWindow.document.write(htmlContent);
  printWindow.document.close();

  // Wait for content to load
  printWindow.onload = () => {
    printWindow.print();
  };
}

/**
 * Bulk export multiple conversations
 */
export async function bulkExportConversations(
  conversationIds: string[],
  format: ExportFormat
): Promise<void> {
  for (const conversationId of conversationIds) {
    await exportConversation({ conversationId, format });
    // Small delay between exports to avoid overwhelming the browser
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

/**
 * Export conversation with toast notification
 */
export async function exportWithNotification(
  options: ExportOptions,
  showToast: (message: string, type: 'success' | 'error') => void
): Promise<void> {
  try {
    await exportConversation(options);
    showToast(`Exported conversation as ${options.format.toUpperCase()}`, 'success');
  } catch (error) {
    showToast(`Failed to export: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
  }
}
