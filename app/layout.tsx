import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI 얼굴 나이 인식 키오스크',
  description: 'Face++ API를 사용한 실시간 얼굴 나이 인식 시스템',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
