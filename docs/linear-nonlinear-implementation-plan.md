# FEA Expert 0.1.10 Linear ve Nonlinear uygulama planı

## Kapsam

Genel lineer statik, parametrik SOL 101, nonlineer malzeme/adım geçmişi, temas ve önyük, solver teşhisi ve sonuç kabulü ayrı girişler alır. Skill metinleri yöntemi ve karar sınırlarını taşır. Sentetik model girdileri ve sayısal doğrulama ayrı fixture ve kalifikasyon belgelerinde tutulur. AgentsAI, Codex ve VS Code aynı kanonik skill ağacını kullanır.

## İş paketleri

| İş paketi | Değişiklik | Tamamlama ölçütü |
|---|---|---|
| Lineer statik | `fea-linear-static` yük yolu, varsayım seçimi, etkin yük/kısıt, fiziksel kontrol ve sonuç recovery kapsamını sahiplenir. `simcenter-parametric-sol101` CAD ilişkilendirme ve parametrik güncellemeyi sahiplenir. | Ana workflow ve AgentsAI, sıradan SOL 101 ile geometrisi değişen ilişkisel çalışmayı ayrı yönlendirir. SOL 101 fixture’ında signed deplasman, reaksiyon ve stress eşleşir. |
| Nonlineer statik | `fea-multistep-nonlinear`, SOL 106/401/402 için etkin kontrolleri, adım bağımlılığını ve malzeme geçmişini tanımlar. `fea-connector-contact`, temas ve bolt preload fiziğini sahiplenir. | Her çözücü için yükleme ve boşaltma adımları ile gerçek durum/alan recovery ayrı gösterilir. Genel convergence bayrağı ile fiziksel sonuç kabulü farklı kanıtlardır. |
| Native kurulum ve saklama | NXOpen üzerinden tam Nastran input’tan bağımsız FEM/SIM üret. FEM ve SIM’e ayrı kök adları ver. Translator ve deck birimlerini doğrula. | Kaydedilen dosyaların hash’leri sabit. Boş batch süreci doğru FEM/SIM bağını ve subcase’leri görüyor. Canlı MCP bağı ve ilk oturumun geri yüklenmesi gözlemleniyor. |
| Solver ve sonuç | Yeniden açılan SIM’den yeni deck dışa aktar. Etkin BC, yük, malzeme, adım kontrolleri ve sonuç isteklerini kontrol et. Aynı byte’ları taze job’da çöz. | F06’da fatal bulunmuyor, beklenen durumlar mevcut ve sonuç dosyası aynı job’a bağlı. Sayısal karşılaştırma, F06 ve BatchPost dosyalarında doğru bileşen, işaret, birim ve recovery konumunu kullanıyor. |
| Dağıtım | 0.1.10 sürüm yüzeylerini ve skill kataloğunu eşitle. Statik route tablosunu üç istemciye taşı. | Kaynak doğrulaması, mevcut testler ve üç istemci paketinin manifest, link ve içerik kontrolleri geçiyor. |

[Statik yönlendirme](../skills/fea-sc3d-tool-routing/references/static-routing.md) · [Native round trip yöntemi](../skills/designcenter-open-journal-authoring/references/static-deck-roundtrip-2612.md)

## Her çözüm için geçiş ölçütü

1. Fiziksel hipotezi, birimleri, minimum ölçülebilir sonucu ve bağımsız referansı belirle.
2. İlgili Help, KB veya Community gözlemini tam deck ve kurulu sürümün API/solver davranışıyla bağla. Dokümantasyonun dönen sürümünü ve native build’i ayrı kaydet.
3. Bağımsız batch save ve reopen, canlı MCP okuma, etkin deck hash’i, terminal F06, gerçek sonuç state’i ve sayısal karşılaştırma için ayrı kanıt üret.
4. Zaman aşımında belirsiz etkiyi yeni readback ile çöz. Sonuç çıktısı boşsa exact job ile format/reader kapsamını kontrol et. Aynı arıza üzerine değişiklik yapmadan yeniden dispatch etme.
5. Fixture kapsamını açık bildir. Bir sonraki çözümün doğrulamasına öncekinin karşılaştırmaları tamamlandıktan sonra geç.

## Siemens kaynaklarının yönteme etkisi

| Konu | Kullanım |
|---|---|
| SOL 101 Pre/Post ve deck import | FEM/SIM kurulumu ve solver input dosyasından sahipli model üretimini ayrı rotalar olarak tanımla. [Assembly FEM setup, KB000121470](https://support.sw.siemens.com/en-US/knowledge-base/KB000121470_EN_US) · [Simcenter 3D import yordamı](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced_sim_tutorial/html/xid1844998?audience=external) |
| SOL 106 plastisite | `NLPARM`, `NLSTRESS` ve bilineer `MATS1` akma alanını etkin export’ta kontrol et. Eski maintenance düzeyindeki bir eksik alan düzeltmesini mevcut build’e otomatik uygulama. [KB000153430](https://support.sw.siemens.com/en-US/knowledge-base/KB000153430_EN_US) · [Siemens Community örneği](https://community.sw.siemens.com/s/question/0D54O00008ACs36SAD) |
| SOL 401 adım geçmişi ve önyük | Ayarlanan ve gerçekten ulaşılan yükleri ayır. Preload sırasında ve servis yükü boyunca bolt işareti ve kuvvetini karşılaştır. [SOL 401 adım sırası](https://docs.sw.siemens.com/en-US/doc/PL20251024315120185.multi_step_nonlinear/html/xid638709?audience=external) · [Önyük sonrası servis adımı, PL8869179](https://support.sw.siemens.com/en-US/knowledge-base/PL8869179) · [Siemens Community plastik sonuç tartışması](https://community.sw.siemens.com/s/question/0D54O00008DRgxWSAT) |
| SOL 402 adım geçmişi | `SEQDEP` ve `RSUB` için aktarılan durum ile zaman koordinatını ayrı doğrula. Negatif pivot görüldüğünde mekanizmayı, teması ve denge yolunu araştır. [NLCNTL2](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.QRG/html/xid1270968?audience=external) · [Adım bağımlılığı](https://docs.sw.siemens.com/en-US/doc/PL20251024315444291.advanced/html/xid2190520?audience=external) · [Negatif pivot, KB000179582](https://support.sw.siemens.com/en-US/knowledge-base/KB000179582_EN_US) · [Siemens Community adım tartışması](https://community.sw.siemens.com/s/question/0D5KZ000000ZqBN0A0) |

Help Server’da 2612 istendi. İlgili kılavuzlar çoğunlukla 2606 olarak döndü. 2612.1700’deki çalışma sırasında gözlenen davranışlar kalifikasyon kaydında belirtilir. [Siemens Structures & Dynamics KB dizini](https://support.sw.siemens.com/en-US/knowledge-base/KB000073922_EN_US)

## Daha geniş model kapsamı için sonraki doğrulamalar

| Kapsam | Kanıtlanacak durum |
|---|---|
| İlişkisel SOL 101 | Bir CAD parametresini değiştir, mesh’i güncelle, aynı fiziksel yük/kısıt bölgelerini yeniden çözümle ve yeni deck ile ikinci sonuç karşılaştırmasını yap. |
| SOL 401 temas ve bolt preload | Kurulum, preload, kilitleme ve servis adımlarında bolt kuvvetini ve temas açıklığı/basıncını bağımsız uyumluluk hesabıyla karşılaştır. Gerekiyorsa maintenance seviyesini KB koşullarıyla bağla. |
| SOL 402 nonsequential restart ve büyük deformasyon | Hedef predecessor ile başlayan state, zaman ekseni, stress ölçüsü ve istenen reject/accept davranışını farklı kontrollü fixture’larla sınayarak belgeye bağla. |
| Lineer ve nonlineer yerel sonuçlar | Eleman türü, mesh/time-step refinement, shell yüzü/ply veya stress ortalaması hedefteyse kabul toleransını ilgili QoI için bağımsız kur. |

[Aktif kalifikasyon kaydı](qualification/0.1.10.md)
