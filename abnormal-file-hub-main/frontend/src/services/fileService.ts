import axios from 'axios';
import { File as FileType, StorageStats } from '../types/file';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export const fileService = {
  async uploadFile(file: File): Promise<FileType> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${API_URL}/files/`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async getFiles(params?: {
    search?: string;
    file_type?: string;
    min_size?: number;
    max_size?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<FileType[]> {
    const response = await axios.get(`${API_URL}/files/`, { params });
    return response.data;
  },

  async getStats(): Promise<StorageStats> {
    const response = await axios.get(`${API_URL}/files/stats/`);
    return response.data;
  },

  async deleteFile(id: string): Promise<void> {
    await axios.delete(`${API_URL}/files/${id}/`);
  },

  async downloadFile(fileUrl: string, filename: string): Promise<void> {
    try {
      const response = await axios.get(fileUrl, {
        responseType: 'blob',
      });

      // Create a blob URL and trigger download
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download error:', error);
      throw new Error('Failed to download file');
    }
  },

  async calculateHash(file: File): Promise<string> {
    const buffer = await file.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  },

  async checkFileExists(fileData: {
    file_hash: string;
    filename: string;
    file_type: string;
    size: number;
  }): Promise<{ exists: boolean; file?: FileType }> {
    const response = await axios.post(`${API_URL}/files/dedup-check/`, fileData);
    return response.data;
  },
}; 