import { NextRequest, NextResponse } from "next/server"

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { imageBase64, frameCount } = body || {}
    
    if (!imageBase64 || typeof imageBase64 !== "string") {
      return NextResponse.json({ error: "imageBase64 required" }, { status: 400 })
    }

    // Face++ API를 사용한 실제 얼굴 인식
    const result = await callFacePlusPlusAPI(imageBase64, frameCount)
    
    return NextResponse.json(result)
  } catch (e: any) {
    return NextResponse.json({ error: e?.message || "Internal error" }, { status: 500 })
  }
}

// Face++ API 호출 함수
async function callFacePlusPlusAPI(imageBase64: string, frameCount: number = 0): Promise<any> {
  try {
    // 환경 변수에서 Face++ API 설정 가져오기
    const API_KEY = process.env.FACE_API_KEY
    const API_SECRET = process.env.FACE_API_SECRET
    
    if (!API_KEY || !API_SECRET) {
      throw new Error("Face++ API 키가 설정되지 않았습니다. .env 파일을 확인하세요.")
    }
    
    const API_URL = 'https://api-us.faceplusplus.com/facepp/v3/detect'
    
    // Base64 이미지 데이터 준비 (data:image/jpeg;base64, 부분 제거)
    const imageData = imageBase64.includes(',') ? imageBase64.split(',')[1] : imageBase64
    
    // FormData 생성
    const formData = new URLSearchParams()
    formData.append('api_key', API_KEY)
    formData.append('api_secret', API_SECRET)
    formData.append('image_base64', imageData)
    formData.append('return_attributes', 'age,gender,smiling,headpose,facequality,blur,eyestatus,emotion,ethnicity,beauty,mouthstatus,eyegaze,skinstatus')
    
    console.log(`[Face++ API] 프레임 ${frameCount} 호출 중...`)
    
    // Face++ API 호출
    const response = await fetch(API_URL, {
      method: 'POST',
      body: formData,
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    
    if (!response.ok) {
      throw new Error(`Face++ API 오류: ${response.status} ${response.statusText}`)
    }
    
    const data = await response.json()
    
    // Face++ 응답 처리
    if (data.error_message) {
      console.error(`[Face++ API] 오류: ${data.error_message}`)
      throw new Error(data.error_message)
    }
    
    if (data.faces && data.faces.length > 0) {
      const face = data.faces[0]
      const attributes = face.attributes || {}
      
      // 나이 추정
      const age = attributes.age ? attributes.age.value : null

      
      console.log(`[Face++ API] 성공: ${age}세`)
      
      return {
        age: age,
        face_detected: true,
        face_count: data.faces.length,
        confidence: "high",
        real_time: true,
        frame: frameCount,
        timestamp: Date.now(),
        method: "faceplusplus_api",
        api_response: data
      }
    } else {
      // 얼굴이 검출되지 않은 경우
      console.log(`[Face++ API] 얼굴 미검출`)
      return {
        age: null,
        gender: "Unknown",
        face_detected: false,
        face_count: 0,
        confidence: "low",
        real_time: true,
        frame: frameCount,
        timestamp: Date.now(),
        method: "faceplusplus_api",
        api_response: data
      }
    }
    
  } catch (error) {
    console.error(`[Face++ API] 오류:`, error)
    
    // 오류 발생 시 기본값 반환
    return {
      age: null,
      gender: "Unknown",
      face_detected: false,
      face_count: 0,
      confidence: "error",
      real_time: false,
      frame: frameCount || 0,
      timestamp: Date.now(),
      method: "faceplusplus_api_error",
      error: error instanceof Error ? error.message : "Unknown error"
    }
  }
}


