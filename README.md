# velog-post skill

GitHub 저장소의 README를 [velog](https://velog.io) 글로 올려 주는 [Claude Code](https://claude.com/claude-code) 스킬입니다.
Claude가 **Claude in Chrome** 확장으로, 이미 velog에 로그인된 내 Chrome에서 글을 직접 작성합니다.

- **공개(PUBLIC) 저장소일 때만** 글을 씁니다. 비공개 저장소는 건너뜁니다.
- README의 상대 경로 이미지·링크를 GitHub 절대 URL로 바꿔서 velog에서도 깨지지 않게 합니다.
- 결과를 확인하면서 찍은 스크린샷을 **썸네일**로 자동 업로드합니다.
- velog가 자동으로 만드는 요약(URL이 `&#x3A;` 로 깨짐)을 깔끔한 문장으로 바꿉니다.

velog에는 공식 API가 없어서, MCP 대신 브라우저를 사람처럼 조작하는 스킬로 만들었습니다.
로그인 정보나 토큰은 저장하지 않습니다. velog 세션은 Chrome에, GitHub 인증은 로컬 `gh` 에 있습니다.

## 준비물

- Claude Code (데스크톱 앱 또는 CLI)
- [Claude in Chrome](https://claude.com/chrome) 확장 연결 + Chrome에서 velog 로그인
- [GitHub CLI](https://cli.github.com/) (`gh auth login` 완료): 저장소 공개 여부 확인용
- Python 3.9+ (표준 라이브러리만 사용)

## 설치

```bash
git clone https://github.com/sedoll/velog-post-skill.git ~/.claude/skills/velog-post
```

Windows(PowerShell):

```powershell
git clone https://github.com/sedoll/velog-post-skill.git "$env:USERPROFILE\.claude\skills\velog-post"
```

Claude Code를 다시 열면 스킬 목록에 `velog-post` 가 나타납니다.

## 사용법

GitHub에 푸시한 프로젝트 폴더에서 Claude에게 이렇게 말하면 됩니다.

```
/velog-post
```

또는 "README 내용으로 velog에 글 써줘", "velog 올려줘" 처럼 요청해도 스킬이 사용됩니다.
기존 글을 고치고 싶으면 글 주소를 같이 알려 주세요. 새 글을 만들지 않고 수정합니다.

### 진행 순서

1. `scripts/readme_to_velog.py` 가 저장소 공개 여부를 확인하고 README를 velog용 마크다운으로 변환
2. Chrome에서 `velog.io/write` 를 열고 제목·본문·태그 입력
3. 출간 패널에서 썸네일 업로드, 요약 정리, 전체 공개로 출간
4. 내 글 목록에서 썸네일과 함께 올라갔는지 확인

### 스크립트만 따로 쓰기

```bash
python scripts/readme_to_velog.py path/to/README.md --out ./velog
```

| 옵션 | 설명 |
| --- | --- |
| `--repo owner/name` | 저장소 지정 (기본: README 폴더의 `origin` 리모트) |
| `--branch main` | 브랜치 지정 (기본: 현재 브랜치) |
| `--no-visibility-check` | 공개 여부 확인 생략 |

출력 파일: `velog.md` (본문), `set_body.js` (velog 에디터에 본문을 넣는 코드), `meta.json` (제목, 이미지 목록 등).
비공개 저장소면 종료 코드 `2` 로 끝나고 아무 파일도 만들지 않습니다.

## 파일 구성

```
SKILL.md                     Claude가 따르는 작업 절차
scripts/readme_to_velog.py   공개 여부 확인 + README → velog 마크다운 변환
scripts/capture_file_input.js 썸네일 업로드용 파일 입력 가로채기 (네이티브 파일 선택창 우회)
```

## 한계

- velog 화면 구조(에디터, 출간 패널)가 바뀌면 `SKILL.md` 의 단계나 스크립트를 고쳐야 할 수 있습니다.
- 이미지는 `raw.githubusercontent.com` 에서 불러오므로, README 이미지가 푸시되어 있어야 합니다.
- Claude in Chrome이 연결된 환경에서만 글을 쓸 수 있습니다.

## 라이선스

[MIT](LICENSE)
