# MongoDB 데이터베이스 구조

## 컬렉션: users

### 스키마
```python
{
    "email": String,          # 필수, 유니크
    "password": String,       # 필수 (bcrypt로 해시된 비밀번호)
    "created_at": DateTime,   # 자동 생성
    "updated_at": DateTime,   # 자동 업데이트
    
    # 코인 잔액
    "bitcoin_balance": Float,    # 기본값 0.0
    "ethereum_balance": Float,   # 기본값 0.0
    "solana_balance": Float,     # 기본값 0.0
    
    # 거래 내역
    "transactions": [           # 배열
        {
            "type": String,     # "deposit" 또는 "withdrawal"
            "coin_type": String, # "bitcoin", "ethereum", "solana"
            "amount": Float,
            "status": String,    # "completed"
            "created_at": DateTime,
            
            # 입금 시
            "tx_hash": String,   # 트랜잭션 해시
            
            # 출금 시
            "destination_address": String  # 출금 주소
        }
    ]
}
```

### 인덱스
- `email`: 유니크 인덱스
- 정렬: `created_at` 내림차순

### 예시 문서
```json
{
    "_id": ObjectId("..."),
    "email": "user@example.com",
    "password": "$2b$12$...",  // bcrypt 해시
    "created_at": ISODate("2024-03-21T10:00:00Z"),
    "updated_at": ISODate("2024-03-21T10:00:00Z"),
    "bitcoin_balance": 1.5,
    "ethereum_balance": 2.0,
    "solana_balance": 0.0,
    "transactions": [
        {
            "type": "deposit",
            "coin_type": "bitcoin",
            "amount": 1.5,
            "tx_hash": "abc123...",
            "status": "completed",
            "created_at": ISODate("2024-03-21T10:00:00Z")
        },
        {
            "type": "withdrawal",
            "coin_type": "ethereum",
            "amount": 0.5,
            "destination_address": "0x123...",
            "status": "completed",
            "created_at": ISODate("2024-03-21T11:00:00Z")
        }
    ]
}
```

### 주요 쿼리 패턴
1. 사용자 조회
   - 이메일로 조회: `User.objects(email=email).first()`
   - ID로 조회: `User.objects(id=user_id).first()`

2. 잔액 업데이트
   - 입금: `setattr(user, f"{coin_type}_balance", current_balance + amount)`
   - 출금: `setattr(user, f"{coin_type}_balance", current_balance - amount)`

3. 거래 내역 추가
   - `user.transactions.append(transaction)`
   - `user.save()`

### 보안 특징
1. 비밀번호는 bcrypt로 해시되어 저장
2. 모든 API 엔드포인트는 JWT 인증 필요
3. 잔액 검증 로직으로 부정 출금 방지

### 확장성 고려사항
1. 거래 내역이 많아질 경우를 대비해 별도 컬렉션으로 분리 고려
2. 코인 종류가 추가될 경우 스키마 수정 필요
3. 거래 상태 관리 (pending, completed, failed 등) 추가 가능