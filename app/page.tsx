export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-800 mb-4">
            👴 AI 얼굴 나이 인식 키오스크
          </h1>
          <p className="text-xl text-gray-600">
            Face++ API를 사용한 실시간 얼굴 나이 인식 시스템
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            🚀 API 상태
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-medium text-green-800 mb-2">✅ API 서버</h3>
              <p className="text-green-600">정상 실행 중</p>
              <p className="text-sm text-green-500 mt-1">포트: 3000</p>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-800 mb-2">🔗 Face++ API</h3>
              <p className="text-blue-600">연결 준비 완료</p>
              <p className="text-sm text-blue-500 mt-1">엔드포인트: /api/face</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            📋 사용 방법
          </h2>
          <div className="space-y-4">
            <div className="flex items-start space-x-3">
              <div className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold">1</div>
              <div>
                <h3 className="font-medium text-gray-800">스트림릿 앱 실행</h3>
                <p className="text-gray-600">터미널에서 <code className="bg-gray-100 px-2 py-1 rounded">streamlit run streamlit_app.py</code> 실행</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold">2</div>
              <div>
                <h3 className="font-medium text-gray-800">카메라로 얼굴 촬영</h3>
                <p className="text-gray-600">5초 카운트다운 후 자동으로 나이 인식</p>
              </div>
            </div>
            <div className="flex items-start space-x-3">
              <div className="bg-blue-500 text-white rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold">3</div>
              <div>
                <h3 className="font-medium text-gray-800">자동 라우팅</h3>
                <p className="text-gray-600">65세 미만: 웹사이트 이동, 65세 이상: 메뉴 선택</p>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            🔧 기술 스택
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">🎯</div>
              <div className="font-medium text-gray-800">Next.js</div>
              <div className="text-sm text-gray-600">API 서버</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">🐍</div>
              <div className="font-medium text-gray-800">Streamlit</div>
              <div className="text-sm text-gray-600">프론트엔드</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">👁️</div>
              <div className="font-medium text-gray-800">Face++</div>
              <div className="text-sm text-gray-600">얼굴 인식</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl mb-2">📱</div>
              <div className="font-medium text-gray-800">OpenCV</div>
              <div className="text-sm text-gray-600">이미지 처리</div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}

