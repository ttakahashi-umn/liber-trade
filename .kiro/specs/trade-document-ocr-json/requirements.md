# Requirements Document

## Introduction
本仕様は、貿易実務担当者および営業事務が扱う書類の「アップロード→OCR抽出→JSON化→数値整合確認」までを対象とする。
会社ごとに異なる書類フォーマットを統一的に取り込み、手動転記を削減することを目的とする。

## Boundary Context (Optional)
- **In scope**: 書類画像の受け付け、抽出結果のJSON化、自社標準フォーマットへの正規化、金額計算の整合確認、確認可能な結果提示
- **Out of scope**: セキュリティ/監査の本格設計、高度な可観測性、本番運用向けの可用性設計、HITL基準の詳細設計
- **Adjacent expectations**: 利用者は対象書類画像を事前に用意すること、後続業務システムは本機能が出力するJSONを受け取れること

## Requirements

### Requirement 1: 書類アップロードと処理開始
**Objective:** As a 貿易実務担当者または営業事務, I want 書類画像をアップロードして処理を開始できること, so that 手動転記を始める前に自動処理へ渡せる

#### Acceptance Criteria
1. When 利用者が対応形式の書類画像をアップロードしたとき, the Document Processing Service shall 受付成功を示し処理を開始する
2. If 利用者が非対応形式または破損ファイルをアップロードしたとき, the Document Processing Service shall 処理を開始せず理由を示すエラーメッセージを返す
3. While 書類が処理中である間, the Document Processing Service shall 利用者が処理中状態を認識できる状態表示を提供する
4. The Document Processing Service shall 受付した書類ごとに一意の処理単位を付与して追跡可能にする

### Requirement 2: OCR抽出とJSON構造化
**Objective:** As a 貿易実務担当者または営業事務, I want 書類内容が構造化JSONとして取得できること, so that 後続処理で再入力せずに活用できる

#### Acceptance Criteria
1. When 書類画像の解析が完了したとき, the Document Processing Service shall テキスト情報および表形式情報を含むJSONを生成する
2. If 書類から必要項目を抽出できないとき, the Document Processing Service shall 抽出不可項目を識別可能な状態でJSONに含める
3. The Document Processing Service shall JSON出力に項目名と値の対応関係を保持する

### Requirement 3: 自社標準フォーマットへの正規化
**Objective:** As a 営業事務, I want 会社ごとに異なる表現を自社標準項目へ揃えられること, so that 書類差分があっても同じ業務フローで扱える

#### Acceptance Criteria
1. When 抽出JSONに会社固有の項目表現が含まれるとき, the Document Processing Service shall 自社標準フォーマットへマッピングしたJSONを出力する
2. If 標準フォーマットへ対応付けできない項目があるとき, the Document Processing Service shall 未対応項目として識別できる情報を返す
3. The Document Processing Service shall 同一意味の項目は入力表現が異なっても同一の標準キーに正規化する

### Requirement 4: 数値整合性チェック
**Objective:** As a 貿易実務担当者, I want 単価・数量・小計・税・合計の整合性を確認できること, so that 金額不整合を早期に検知できる

#### Acceptance Criteria
1. When 明細行に単価と数量が存在するとき, the Document Processing Service shall 単価 x 数量と小計の一致可否を判定する
2. When 小計と税額と合計が存在するとき, the Document Processing Service shall 合計の整合可否を判定する
3. If いずれかの整合判定が不一致のとき, the Document Processing Service shall 不一致箇所と期待値を利用者が判別可能な形で返す
4. The Document Processing Service shall 判定結果をJSON出力に含める

### Requirement 5: 結果確認と再処理判断
**Objective:** As a 貿易実務担当者または営業事務, I want 抽出結果と整合判定結果を確認して次アクションを判断できること, so that 業務利用可否を迅速に決められる

#### Acceptance Criteria
1. When 利用者が処理結果を参照するとき, the Document Processing Service shall 正規化JSONと整合判定結果を同時に提示する
2. If 抽出不足または不整合が検出されたとき, the Document Processing Service shall 再確認または再処理が必要であることを明示する
3. The Document Processing Service shall 処理成功・要確認・失敗の状態を利用者が区別できる形で返す

### Requirement 6: 画像主系 + テキスト補正副系
**Objective:** As a 貿易実務担当者または営業事務, I want 帳票形式差分に強い抽出をしたい, so that 画像埋め込み帳票でもMVPとして安定運用できる

#### Acceptance Criteria
1. When 入力が PDF または Excel のとき, the Document Processing Service shall 一度画像化して Vision OCR の主系フローへ投入する
2. Where 補助テキストが取得可能な場合, the Document Processing Service shall OCR 結果を補正するために補助テキストを利用できる
3. If 主系結果と補助テキスト補正結果に不一致があるとき, the Document Processing Service shall 利用者が要確認と判断できる状態を返す
