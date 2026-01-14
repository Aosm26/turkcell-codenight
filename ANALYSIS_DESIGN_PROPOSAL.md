# Analiz ve Atama Modülü Tasarım Önerisi

Case dokümanına dayanarak, sistemin "Analiz" kısmının 4 aşamalı bir "Pipeline" (Boru Hattı) mimarisinde çalışmasını öneriyorum.

## Akış Şeması

```mermaid
graph TD
    A[Ham Talep (Request)] -->|1. Zenginleştirme| B(Zenginleştirilmiş Veri)
    B -->|2. Skorlama| C(Öncelik Skoru - Priority Score)
    C -->|3. Kaynak Süzme| D(Aday Kaynaklar)
    D -->|4. Karar & Atama| E{Uygun Kaynak Var mı?}
    E -->|Evet| F[Atama Yap (Logla & Kapasite Düş)]
    E -->|Hayır| G[Bekleme Kuyruğuna Al]
```

## Detaylı Analiz Adımları

### 1. Veri Zenginleştirme (Data Enrichment)
Sistemin doğru karar verebilmesi için sadece talep verisi yetmez.
*   **Girdi:** `requests.csv` satırı.
*   **İşlem:**
    *   `users.csv` ile eşleştir -> Kullanıcının **Şehri** bulunur.
    *   `timestamp` kontrolü -> Şu anki zamanla fark alınıp **Bekleme Süresi (Waiting Hours)** hesaplanır.
*   **Çıktı:** Kullanıcı şehri ve bekleme süresini içeren "Zengin Talep Nesnesi".

### 2. Öncelik Analizi ve Skorlama (Scoring Analysis)
Tanımladığımız kuralların uygulandığı yerdir.
*   **Girdi:** Zengin Talep Nesnesi + `allocation_rules.csv`
*   **İşlem:**
    *   Veri tabanındaki aktif kurallar tek tek gezilir.
    *   Eğer talep, kuralın `condition` (koşul) kısmına uyuyorsa, kuralın `weight` (puanı) toplama eklenir.
*   **Çıktı:** Tek bir sayısal `priority_score` (Örn: 130).

### 3. Kaynak Uygunluk Analizi (Resource Viability Analysis)
Hangi kaynağın bu işi yapabileceğine karar verilir.
*   **Girdi:** `resources.csv`
*   **Filtreler:**
    1.  **Statü:** Sadece `AVAILABLE` olanlar.
    2.  **Kapasite:** `capacity > 0` olanlar.
    3.  **Yetkinlik (Hard Constraint):**
        *   `CONNECTION_ISSUE`, `SPEED_COMPLAINT` -> Sadece **TECH_TEAM**
        *   `PAYMENT_PROBLEM`, `STREAMING_ISSUE` -> Sadece **SUPPORT_AGENT**
    4.  **Lokasyon (Soft Constraint):**
        *   Talep eden kullanıcının şehri ile kaynağın şehri aynı mı? Öncelik aynı olanda olmalı.

### 4. Atama Kararı ve Çatışma Çözümü (Allocation Decision)
*   **Çatışma Senaryosu:** İki farklı talep aynı anda tek bir kaynağa göz dikerse?
*   **Kural:** `priority_score` değeri yüksek olan kazanır.
*   **Aksiyon:**
    *   En yüksek puanlı talep için en uygun (örn: aynı şehirdeki) kaynak seçilir.
    *   Kaynağın kapasitesi 1 azaltılır.
    *   `allocations.csv` dosyasına yeni kayıt atılır.
    *   Atanamayan talep için log basılır: "Yetersiz Kaynak - Sırada Bekliyor".

## Öneri
Bu yapıyı Python'da `AllocationService` isimli bir sınıf (class) içinde toplamak en temiz yöntem olacaktır.
